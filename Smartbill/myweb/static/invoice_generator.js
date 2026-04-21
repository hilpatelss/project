/**
 * Invoice PDF Generator
 * Requires: jsPDF (https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js)
 *
 * Usage from Django template:
 *   generateInvoicePDF(invoiceData);
 *
 * All fields are passed via the `invoiceData` object — fill from Django context.
 */

function generateInvoicePDF(data) {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "pt", format: "a4" });

  const PW = 595.28; // A4 width in points
  const PH = 841.89; // A4 height in points
  const ML = 40;     // margin left
  const MR = PW - 40; // margin right

  // ─── Helpers ───────────────────────────────────────────────────────────────
  const setFont = (style = "normal", size = 10) => {
    doc.setFont("helvetica", style);
    doc.setFontSize(size);
  };

  const text = (str, x, y, opts = {}) => doc.text(String(str ?? ""), x, y, opts);

  const line = (x1, y1, x2, y2, color = [0, 0, 0]) => {
    doc.setDrawColor(...color);
    doc.line(x1, y1, x2, y2);
  };

  const rect = (x, y, w, h, fill = [0, 0, 0]) => {
    doc.setFillColor(...fill);
    doc.rect(x, y, w, h, "F");
  };

  // ─── HEADER (black bar) ────────────────────────────────────────────────────
  rect(0, 0, PW, 120, [20, 20, 20]);

  // Store name
  setFont("bold", 20);
  doc.setTextColor(255, 255, 255);
  text(data.store_name || "SmartBill Store", ML + 10, 40);

  // Tagline
  setFont("normal", 9);
  doc.setTextColor(180, 180, 180);
  text(data.store_tagline || "Your trusted local shop", ML + 10, 56);

  // Store address / phone / GSTIN
  setFont("normal", 8);
  doc.setTextColor(200, 200, 200);
  text(data.store_address || "", ML + 10, 70);
  text(data.store_phone || "", ML + 10, 82);
  text(data.store_gstin || "", ML + 10, 94);

  // INVOICE label (right)
  setFont("bold", 28);
  doc.setTextColor(255, 255, 255);
  text("INVOICE", MR, 38, { align: "right" });

  // Invoice number
  setFont("normal", 10);
  doc.setTextColor(180, 180, 180);
  text(`#${data.invoice_number || "INV-1"}`, MR, 56, { align: "right" });

  // Payment status badge (white text on dark)
  const status = data.payment_status || "Pending";
  setFont("bold", 10);
  doc.setTextColor(255, 255, 255);
  text(status, MR, 74, { align: "right" });

  // ─── BILLED TO / DATES / PAYMENT ──────────────────────────────────────────
  let y = 145;
  doc.setTextColor(0, 0, 0);

  // Column x positions
  const col1 = ML;
  const col2 = 220;
  const col3 = 390;

  // Labels
  setFont("normal", 7);
  doc.setTextColor(120, 120, 120);
  text("BILLED TO", col1, y);
  text("INVOICE DATE", col2, y);
  text("PAYMENT METHOD", col3, y);

  y += 14;
  setFont("bold", 11);
  doc.setTextColor(0, 0, 0);
  text(data.client_name || "", col1, y);

  setFont("bold", 11);
  text(data.invoice_date || "", col2, y);

  setFont("normal", 11);
  text(data.payment_method || "Cash", col3, y);

  y += 14;
  setFont("normal", 9);
  doc.setTextColor(60, 60, 60);
  text(data.client_phone || "", col1, y);

  // Due date label
  setFont("normal", 7);
  doc.setTextColor(120, 120, 120);
  text("DUE DATE", col2, y);

  // Payment status label
  text("PAYMENT STATUS", col3, y);

  y += 12;
  setFont("bold", 11);
  doc.setTextColor(0, 0, 0);
  text(data.client_email || "", col1, y);
  text(data.due_date || "", col2, y);

  // Payment status value (bold)
  setFont("bold", 11);
  text(status, col3, y);

  // ─── Divider ───────────────────────────────────────────────────────────────
  y += 20;
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.5);
  line(ML, y, MR, y);

  // ─── TABLE HEADER ──────────────────────────────────────────────────────────
  y += 16;
  rect(ML, y - 12, MR - ML, 20, [240, 240, 240]);

  const COL = {
    num:   ML + 10,
    desc:  ML + 50,
    price: ML + 250,
    gst:   ML + 340,
    qty:   ML + 400,
    total: MR - 10,
  };

  setFont("bold", 8);
  doc.setTextColor(80, 80, 80);
  text("#",             COL.num,   y);
  text("PRODUCT / DESCRIPTION", COL.desc, y);
  text("UNIT PRICE",   COL.price, y);
  text("GST %",        COL.gst,   y);
  text("QTY",          COL.qty,   y);
  text("TOTAL",        COL.total, y, { align: "right" });

  // ─── TABLE ROWS ────────────────────────────────────────────────────────────
  y += 18;
  const items = data.items || [];

  items.forEach((item, idx) => {
    if (idx % 2 === 1) {
      rect(ML, y - 12, MR - ML, 18, [248, 248, 248]);
    }

    setFont("normal", 10);
    doc.setTextColor(0, 0, 0);
    text(idx + 1,                        COL.num,   y);
    text(item.description || "",         COL.desc,  y);
    text(formatCurrency(item.unit_price), COL.price, y);
    text(`${item.gst_percent || 0}%`,    COL.gst,   y);
    text(item.qty || 1,                  COL.qty,   y);

    setFont("bold", 10);
    text(formatCurrency(item.total),     COL.total, y, { align: "right" });

    y += 20;
  });

  // ─── Divider ───────────────────────────────────────────────────────────────
  y += 6;
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.5);
  line(ML, y, MR, y);

  // ─── TOTALS ────────────────────────────────────────────────────────────────
  y += 20;
  const labelX = MR - 160;
  const valueX = MR;

  const totalsRow = (label, value, bold = false) => {
    setFont(bold ? "bold" : "normal", 10);
    doc.setTextColor(bold ? 0 : 80, bold ? 0 : 80, bold ? 0 : 80);
    text(label, labelX, y);
    text(formatCurrency(value), valueX, y, { align: "right" });
    y += 18;
  };

  totalsRow("Subtotal",                  data.subtotal);
  totalsRow("GST Amount",                data.gst_amount);
  totalsRow(`Discount (${data.discount_percent || 0}%)`, data.discount_amount || 0);

  // Bold total line
  doc.setDrawColor(0);
  doc.setLineWidth(0.8);
  line(labelX, y - 4, MR, y - 4);

  setFont("bold", 12);
  doc.setTextColor(0, 0, 0);
  text("Total Amount",          labelX, y + 10);
  text(formatCurrency(data.total_amount), valueX, y + 10, { align: "right" });

  // ─── NOTES ─────────────────────────────────────────────────────────────────
  y += 40;
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.5);
  doc.roundedRect(ML, y, MR - ML, 52, 3, 3, "S");

  setFont("bold", 9);
  doc.setTextColor(60, 60, 60);
  text("NOTES", ML + 12, y + 16);

  setFont("normal", 9);
  doc.setTextColor(80, 80, 80);
  const noteLines = doc.splitTextToSize(
    data.notes || "Thank you for your purchase!",
    MR - ML - 24
  );
  doc.text(noteLines, ML + 12, y + 30);

  // ─── FOOTER ────────────────────────────────────────────────────────────────
  setFont("normal", 8);
  doc.setTextColor(150, 150, 150);
  text(
    "This is a computer-generated invoice. No signature required.",
    PW / 2,
    PH - 24,
    { align: "center" }
  );

  // ─── Save ──────────────────────────────────────────────────────────────────
  const filename = `Invoice_${data.invoice_number || "INV"}.pdf`;
  doc.save(filename);
}

// ─── Currency formatter ──────────────────────────────────────────────────────
function formatCurrency(amount) {
  const num = parseFloat(amount) || 0;
  return "\u20B9" + num.toFixed(2);
}


// ─── DJANGO INTEGRATION EXAMPLE ─────────────────────────────────────────────
//
// In your Django template, render JSON data into a JS variable and call:
//
//   <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
//   <script src="{% static 'js/invoice_generator.js' %}"></script>
//   <script>
//     const invoiceData = {{ invoice_json|safe }};  // Django renders this
//     document.getElementById('download-btn').addEventListener('click', () => {
//       generateInvoicePDF(invoiceData);
//     });
//   </script>
//
// invoiceData object shape (populate from Django view):
// {
//   store_name:       "SmartBill Store",
//   store_tagline:    "Your trusted local shop",
//   store_address:    "N-156, New Green City",
//   store_phone:      "9265186613",
//   store_gstin:      "27AABCU9603R1ZM",
//
//   invoice_number:   "INV-5",
//   invoice_date:     "April 10, 2026",
//   due_date:         "April 25, 2026",
//   payment_method:   "Cash",
//   payment_status:   "Pending",
//
//   client_name:      "Hil Patel",
//   client_phone:     "9265186613",
//   client_email:     "hilpatelss@gmail.com",
//
//   items: [
//     {
//       description:  "Huio",
//       unit_price:   18.00,
//       gst_percent:  12,
//       qty:          1,
//       total:        20.16
//     }
//   ],
//
//   subtotal:         18.00,
//   gst_amount:       2.16,
//   discount_percent: 0,
//   discount_amount:  0.00,
//   total_amount:     20.16,
//
//   notes: "Thank you for your purchase! For queries, contact us at shop@SmartBill.in"
// }
