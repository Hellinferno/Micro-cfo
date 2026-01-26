#!/usr/bin/env python3
"""
ERP Adapters for MicroCFO
Provides export functionality for Tally, Zoho Books, and Excel/CSV
"""

import logging
import csv
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from io import StringIO, BytesIO

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class InvoiceExportData(BaseModel):
    """Standardized invoice data for export"""
    invoice_number: str
    invoice_date: str
    vendor_name: str
    vendor_gstin: Optional[str] = None
    total_amount: float
    tax_amount: float
    taxable_amount: float
    line_items: List[Dict[str, Any]]
    payment_terms: Optional[str] = None
    due_date: Optional[str] = None


class TallyAdapter:
    """
    Adapter for Tally ERP 9 / Tally Prime
    Generates XML in Tally's voucher import format
    """
    
    @staticmethod
    def generate_xml(invoice: InvoiceExportData) -> str:
        """
        Generate Tally XML for purchase voucher import
        
        Args:
            invoice: Invoice data to export
            
        Returns:
            XML string in Tally format
        """
        # Create root element
        envelope = ET.Element("ENVELOPE")
        
        # Header
        header = ET.SubElement(envelope, "HEADER")
        ET.SubElement(header, "TALLYREQUEST").text = "Import Data"
        
        # Body
        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        
        # Voucher
        tallymessage = ET.SubElement(request_data, "TALLYMESSAGE", xmlns="TallyUDF")
        voucher = ET.SubElement(tallymessage, "VOUCHER", 
                               REMOTEID="", VCHKEY="", VCHTYPE="Purchase", 
                               ACTION="Create", OBJVIEW="Invoice Voucher View")
        
        # Voucher details
        ET.SubElement(voucher, "DATE").text = TallyAdapter._format_date(invoice.invoice_date)
        ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Purchase"
        ET.SubElement(voucher, "VOUCHERNUMBER").text = invoice.invoice_number
        ET.SubElement(voucher, "PARTYLEDGERNAME").text = invoice.vendor_name
        ET.SubElement(voucher, "PERSISTEDVIEW").text = "Invoice Voucher View"
        
        # Line items (Ledger entries)
        all_ledgers_list = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        
        # Vendor ledger (credit)
        ledger_vendor = ET.SubElement(all_ledgers_list, "LEDGER")
        ET.SubElement(ledger_vendor, "LEDGERNAME").text = invoice.vendor_name
        ET.SubElement(ledger_vendor, "ISDEEMEDPOSITIVE").text = "No"
        ET.SubElement(ledger_vendor, "AMOUNT").text = f"-{invoice.total_amount:.2f}"
        
        # Purchase ledger (debit)
        ledger_purchase = ET.SubElement(all_ledgers_list, "LEDGER")
        ET.SubElement(ledger_purchase, "LEDGERNAME").text = "Purchase Account"
        ET.SubElement(ledger_purchase, "ISDEEMEDPOSITIVE").text = "Yes"
        ET.SubElement(ledger_purchase, "AMOUNT").text = f"{invoice.taxable_amount:.2f}"
        
        # Tax ledger (debit) if applicable
        if invoice.tax_amount > 0:
            ledger_tax = ET.SubElement(all_ledgers_list, "LEDGER")
            ET.SubElement(ledger_tax, "LEDGERNAME").text = "GST Input"
            ET.SubElement(ledger_tax, "ISDEEMEDPOSITIVE").text = "Yes"
            ET.SubElement(ledger_tax, "AMOUNT").text = f"{invoice.tax_amount:.2f}"
        
        # Convert to pretty XML string
        xml_str = minidom.parseString(ET.tostring(envelope)).toprettyxml(indent="  ")
        
        logger.info(f"Generated Tally XML for invoice {invoice.invoice_number}")
        return xml_str
    
    @staticmethod
    def _format_date(date_str: str) -> str:
        """
        Convert date to Tally format (YYYYMMDD)
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Date in YYYYMMDD format
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%Y%m%d")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}, using today")
            return datetime.now().strftime("%Y%m%d")
    
    @staticmethod
    def generate_csv_for_tally(invoices: List[InvoiceExportData]) -> str:
        """
        Generate CSV formatted for Tally import
        
        Args:
            invoices: List of invoices to export
            
        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Date", "Voucher Type", "Voucher No", "Party Name", 
            "Ledger", "Amount", "Dr/Cr", "Narration"
        ])
        
        # Data rows
        for invoice in invoices:
            date = invoice.invoice_date
            voucher_no = invoice.invoice_number
            party = invoice.vendor_name
            
            # Vendor entry (Credit)
            writer.writerow([
                date, "Purchase", voucher_no, party,
                party, f"{invoice.total_amount:.2f}", "Cr",
                f"Purchase from {party}"
            ])
            
            # Purchase entry (Debit)
            writer.writerow([
                date, "Purchase", voucher_no, party,
                "Purchase Account", f"{invoice.taxable_amount:.2f}", "Dr",
                f"Purchase from {party}"
            ])
            
            # Tax entry (Debit)
            if invoice.tax_amount > 0:
                writer.writerow([
                    date, "Purchase", voucher_no, party,
                    "GST Input", f"{invoice.tax_amount:.2f}", "Dr",
                    f"GST on purchase from {party}"
                ])
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"Generated Tally CSV for {len(invoices)} invoices")
        return csv_content


class ZohoBooksAdapter:
    """
    Adapter for Zoho Books API
    Generates JSON payload for Zoho Books bill creation
    """
    
    @staticmethod
    def generate_bill_payload(invoice: InvoiceExportData) -> Dict[str, Any]:
        """
        Generate Zoho Books API payload for bill creation
        
        Args:
            invoice: Invoice data to export
            
        Returns:
            Dictionary payload for Zoho Books API
        """
        # Map line items
        line_items = []
        for item in invoice.line_items:
            line_items.append({
                "item_id": "",  # To be filled by user or mapped
                "name": item.get("description", "Item"),
                "description": item.get("description", ""),
                "rate": item.get("amount", 0),
                "quantity": 1,
                "tax_id": "",  # To be filled based on tax configuration
            })
        
        # Create bill payload
        payload = {
            "vendor_name": invoice.vendor_name,
            "bill_number": invoice.invoice_number,
            "date": invoice.invoice_date,
            "due_date": invoice.due_date or invoice.invoice_date,
            "line_items": line_items,
            "notes": f"Imported from MicroCFO - Invoice {invoice.invoice_number}",
            "terms": invoice.payment_terms or "",
        }
        
        # Add GSTIN if available
        if invoice.vendor_gstin:
            payload["gst_treatment"] = "business_gst"
            payload["gst_no"] = invoice.vendor_gstin
        
        logger.info(f"Generated Zoho Books payload for invoice {invoice.invoice_number}")
        return payload
    
    @staticmethod
    def generate_batch_payload(invoices: List[InvoiceExportData]) -> List[Dict[str, Any]]:
        """
        Generate batch payload for multiple invoices
        
        Args:
            invoices: List of invoices to export
            
        Returns:
            List of bill payloads
        """
        return [ZohoBooksAdapter.generate_bill_payload(inv) for inv in invoices]


class ExcelCSVAdapter:
    """
    Adapter for Excel/CSV export
    Generates standardized CSV for general accounting software
    """
    
    @staticmethod
    def generate_csv(invoices: List[InvoiceExportData], include_line_items: bool = False) -> str:
        """
        Generate CSV export for invoices
        
        Args:
            invoices: List of invoices to export
            include_line_items: Whether to include line item details
            
        Returns:
            CSV string
        """
        output = StringIO()
        writer = csv.writer(output)
        
        if include_line_items:
            # Detailed format with line items
            writer.writerow([
                "Invoice Number", "Invoice Date", "Vendor Name", "Vendor GSTIN",
                "Item Description", "Item Amount", "Tax Amount", "Total Amount",
                "Due Date", "Payment Terms"
            ])
            
            for invoice in invoices:
                for item in invoice.line_items:
                    writer.writerow([
                        invoice.invoice_number,
                        invoice.invoice_date,
                        invoice.vendor_name,
                        invoice.vendor_gstin or "",
                        item.get("description", ""),
                        f"{item.get('amount', 0):.2f}",
                        f"{invoice.tax_amount:.2f}",
                        f"{invoice.total_amount:.2f}",
                        invoice.due_date or "",
                        invoice.payment_terms or ""
                    ])
        else:
            # Summary format
            writer.writerow([
                "Invoice Number", "Invoice Date", "Vendor Name", "Vendor GSTIN",
                "Taxable Amount", "Tax Amount", "Total Amount", "Due Date", "Payment Terms"
            ])
            
            for invoice in invoices:
                writer.writerow([
                    invoice.invoice_number,
                    invoice.invoice_date,
                    invoice.vendor_name,
                    invoice.vendor_gstin or "",
                    f"{invoice.taxable_amount:.2f}",
                    f"{invoice.tax_amount:.2f}",
                    f"{invoice.total_amount:.2f}",
                    invoice.due_date or "",
                    invoice.payment_terms or ""
                ])
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"Generated CSV for {len(invoices)} invoices")
        return csv_content
    
    @staticmethod
    def generate_json(invoices: List[InvoiceExportData]) -> str:
        """
        Generate JSON export for invoices
        
        Args:
            invoices: List of invoices to export
            
        Returns:
            JSON string
        """
        data = {
            "export_date": datetime.now().isoformat(),
            "invoice_count": len(invoices),
            "invoices": [inv.dict() for inv in invoices]
        }
        
        logger.info(f"Generated JSON for {len(invoices)} invoices")
        return json.dumps(data, indent=2)


class ERPExportManager:
    """
    Manager for ERP export operations
    Provides unified interface for all export formats
    """
    
    SUPPORTED_FORMATS = ["tally_xml", "tally_csv", "zoho_books", "csv", "json"]
    
    @staticmethod
    def export(
        invoices: List[InvoiceExportData],
        format: str,
        **kwargs
    ) -> str:
        """
        Export invoices to specified format
        
        Args:
            invoices: List of invoices to export
            format: Export format (tally_xml, tally_csv, zoho_books, csv, json)
            **kwargs: Additional format-specific options
            
        Returns:
            Exported data as string
            
        Raises:
            ValueError: If format is not supported
        """
        if format not in ERPExportManager.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Supported formats: {', '.join(ERPExportManager.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"Exporting {len(invoices)} invoices to {format}")
        
        if format == "tally_xml":
            # Export single invoice as XML (Tally limitation)
            if len(invoices) != 1:
                raise ValueError("Tally XML export supports only one invoice at a time")
            return TallyAdapter.generate_xml(invoices[0])
        
        elif format == "tally_csv":
            return TallyAdapter.generate_csv_for_tally(invoices)
        
        elif format == "zoho_books":
            # Return as JSON array
            payloads = ZohoBooksAdapter.generate_batch_payload(invoices)
            return json.dumps(payloads, indent=2)
        
        elif format == "csv":
            include_line_items = kwargs.get("include_line_items", False)
            return ExcelCSVAdapter.generate_csv(invoices, include_line_items)
        
        elif format == "json":
            return ExcelCSVAdapter.generate_json(invoices)
        
        else:
            raise ValueError(f"Format {format} not implemented")
    
    @staticmethod
    def get_format_info(format: str) -> Dict[str, Any]:
        """
        Get information about export format
        
        Args:
            format: Export format
            
        Returns:
            Dictionary with format information
        """
        format_info = {
            "tally_xml": {
                "name": "Tally XML",
                "description": "XML format for Tally ERP 9 / Tally Prime import",
                "file_extension": ".xml",
                "mime_type": "application/xml",
                "supports_batch": False,
                "notes": "Import via Gateway of Tally > Import > Vouchers"
            },
            "tally_csv": {
                "name": "Tally CSV",
                "description": "CSV format for Tally import",
                "file_extension": ".csv",
                "mime_type": "text/csv",
                "supports_batch": True,
                "notes": "Import via Gateway of Tally > Import > Vouchers (CSV)"
            },
            "zoho_books": {
                "name": "Zoho Books JSON",
                "description": "JSON payload for Zoho Books API",
                "file_extension": ".json",
                "mime_type": "application/json",
                "supports_batch": True,
                "notes": "Use with Zoho Books API /bills endpoint"
            },
            "csv": {
                "name": "Standard CSV",
                "description": "Generic CSV format for Excel/accounting software",
                "file_extension": ".csv",
                "mime_type": "text/csv",
                "supports_batch": True,
                "notes": "Compatible with most accounting software"
            },
            "json": {
                "name": "JSON Export",
                "description": "JSON format with complete invoice data",
                "file_extension": ".json",
                "mime_type": "application/json",
                "supports_batch": True,
                "notes": "For custom integrations and data backup"
            }
        }
        
        return format_info.get(format, {})


# Convenience functions
def export_to_tally_xml(invoice: InvoiceExportData) -> str:
    """Export single invoice to Tally XML"""
    return TallyAdapter.generate_xml(invoice)


def export_to_tally_csv(invoices: List[InvoiceExportData]) -> str:
    """Export invoices to Tally CSV"""
    return TallyAdapter.generate_csv_for_tally(invoices)


def export_to_zoho_books(invoices: List[InvoiceExportData]) -> str:
    """Export invoices to Zoho Books JSON"""
    payloads = ZohoBooksAdapter.generate_batch_payload(invoices)
    return json.dumps(payloads, indent=2)


def export_to_csv(invoices: List[InvoiceExportData], include_line_items: bool = False) -> str:
    """Export invoices to CSV"""
    return ExcelCSVAdapter.generate_csv(invoices, include_line_items)


if __name__ == "__main__":
    # Test export functionality
    print("="*60)
    print("ERP ADAPTERS TEST")
    print("="*60)
    
    # Sample invoice data
    sample_invoice = InvoiceExportData(
        invoice_number="INV-2026-001",
        invoice_date="2026-01-18",
        vendor_name="ABC Suppliers Pvt Ltd",
        vendor_gstin="27AABCU9603R1ZM",
        total_amount=11800.00,
        tax_amount=1800.00,
        taxable_amount=10000.00,
        line_items=[
            {"description": "Raw Materials", "amount": 10000.00, "category": "Materials"}
        ],
        payment_terms="Net 30",
        due_date="2026-02-17"
    )
    
    # Test Tally XML
    print("\n1. Tally XML Export:")
    print("-" * 60)
    tally_xml = export_to_tally_xml(sample_invoice)
    print(tally_xml[:500] + "..." if len(tally_xml) > 500 else tally_xml)
    
    # Test Tally CSV
    print("\n2. Tally CSV Export:")
    print("-" * 60)
    tally_csv = export_to_tally_csv([sample_invoice])
    print(tally_csv)
    
    # Test Zoho Books
    print("\n3. Zoho Books JSON Export:")
    print("-" * 60)
    zoho_json = export_to_zoho_books([sample_invoice])
    print(zoho_json)
    
    # Test Standard CSV
    print("\n4. Standard CSV Export:")
    print("-" * 60)
    standard_csv = export_to_csv([sample_invoice])
    print(standard_csv)
    
    print("\n✅ All export formats tested successfully")
