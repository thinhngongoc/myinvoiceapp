function formatCurrency(amount) {
    if (typeof amount !== 'number' || isNaN(amount)) {
        amount = 0;
    }
    // Định dạng số trước, sau đó thêm VNĐ vào cuối
    const formattedNumber = new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);

    return `${formattedNumber} đ`; // Thêm " VNĐ" vào sau số đã định dạng
}

// Hàm định dạng số theo kiểu Mỹ (ví dụ: 123,456.78)
// Dùng cho các số không phải tiền tệ nhưng cần định dạng phần nghìn/thập phân
function formatNumber(num) {
    if (typeof num !== 'number' || isNaN(num)) {
        return '0'; // Hoặc giá trị mặc định khác
    }
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(num);
}
function parseFormattedNumber(str) {
    console.log(`parseFormattedNumber input: "${str}" (type: ${typeof str})`);
    if (typeof str !== 'string') {
        const result = parseFloat(str) || 0;
        console.log(`parseFormattedNumber output (non-string): ${result}`);
        return result;
    }
    const cleanedStr = str.replace(/,/g, ''); // Xóa dấu phẩy
    const result = parseFloat(cleanedStr) || 0;
    console.log(`parseFormattedNumber output (string, cleaned: "${cleanedStr}"): ${result}`);
    return result;
}
// Hàm chuyển đổi số thành chữ tiếng Việt
function convertNumberToVietnameseText(number) {
    if (number === 0) return "Không đồng";

    const units = [
        "không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"
    ];
    const tens = ["", "mười", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"];
    const levels = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ", "triệu tỷ", "tỷ tỷ"]; // Mức độ (nghìn, triệu, tỷ)

    function readThreeDigits(num) {
        let str = "";
        const h = Math.floor(num / 100);
        const t = Math.floor((num % 100) / 10);
        const u = num % 10;

        if (h > 0) {
            str += units[h] + " trăm ";
        }

        if (t === 0 && u === 0) {
            // Nothing to do
        } else if (t === 0) {
            str += (h > 0 ? "linh " : "") + units[u];
        } else if (t === 1) {
            str += "mười ";
            if (u === 5) str += "lăm";
            else if (u > 0) str += units[u];
        } else {
            str += units[t] + " mươi ";
            if (u === 1) str += "mốt";
            else if (u === 5) str += "lăm";
            else if (u > 0) str += units[u];
        }
        return str.trim();
    }

    let result = "";
    let absNumber = Math.abs(number); // Lấy giá trị tuyệt đối để xử lý số âm sau
    let integerPart = Math.floor(absNumber); // Phần nguyên
    let decimalPart = Math.round((absNumber - integerPart) * 100); // Phần thập phân (lấy 2 chữ số)

    if (integerPart === 0 && decimalPart === 0) {
        return "Không đồng";
    }

    // Đọc phần nguyên
    let i = 0;
    while (integerPart > 0) {
        const threeDigits = integerPart % 1000;
        if (threeDigits !== 0) {
            let chunk = readThreeDigits(threeDigits) + " " + levels[i];
            result = chunk.trim() + " " + result;
        }
        integerPart = Math.floor(integerPart / 1000);
        i++;
    }

    result = result.trim();

    // Xử lý phần thập phân (nếu có)
    if (decimalPart > 0) {
        let decimalText = "";
        const t = Math.floor(decimalPart / 10);
        const u = decimalPart % 10;

        if (t === 0) { // Ví dụ: 0.05 (năm xu)
            decimalText = "linh " + units[u];
        } else if (t === 1) { // Ví dụ: 0.15 (mười lăm xu)
            decimalText = "mười ";
            if (u === 5) decimalText += "lăm";
            else if (u > 0) decimalText += units[u];
        } else { // Ví dụ: 0.25 (hai mươi lăm xu)
            decimalText = units[t] + " mươi ";
            if (u === 1) decimalText += "mốt";
            else if (u === 5) decimalText += "lăm";
            else if (u > 0) decimalText += units[u];
        }
        result += (result ? " phẩy " : "") + decimalText + " xu";
    } else {
        result += " đồng";
    }


    // Xử lý số âm
    if (number < 0) {
        result = "âm " + result;
    }

    // Xử lý các trường hợp đặc biệt (ví dụ: "một đồng không xu" -> "một đồng")
    result = result.replace(/một mươi/g, 'mười'); // Đảm bảo 'mười một' thay vì 'một mươi một'
    result = result.replace(/không trăm không/g, 'không trăm'); // Cleanup
    result = result.replace(/\s+/g, ' ').trim(); // Loại bỏ khoảng trắng thừa

    // Đảm bảo "lẻ" thay vì "linh" cho các trường hợp thích hợp
    result = result.replace(/linh (\w+)$/, 'lẻ $1'); // Ví dụ: "hai trăm linh năm" -> "hai trăm lẻ năm"

    // Chuẩn hóa một số trường hợp đặc biệt (thường gặp)
    result = result.replace(/mốt đồng$/, 'một đồng');
    result = result.replace(/mốt nghìn$/, 'một nghìn');
    result = result.replace(/mốt triệu$/, 'một triệu');
    result = result.replace(/mốt tỷ$/, 'một tỷ');
    result = result.replace(/lăm$/, 'lăm'); // Đảm bảo lăm không bị đổi thành năm cuối cùng
    result = result.replace(/năm mươi lăm/g, 'năm mươi lăm'); // Đảm bảo "năm mươi lăm"
    result = result.replace(/mươi năm/g, 'mươi lăm'); // 25, 35 ...

    // Xử lý trường hợp "linh không"
    result = result.replace(/linh không/, '');
    result = result.replace(/mươi không/g, 'mươi'); // 20, 30 ...

    // Chữ cái đầu tiên viết hoa
    return result.charAt(0).toUpperCase() + result.slice(1);
}
function showInvoiceDetailModal(invoiceData) {
    // 1. Điền thông tin chung của hóa đơn
    $('#modalInvoiceMahd').text(invoiceData.mahd);
    $('#detailMahd').text(invoiceData.mahd);
    $('#detailTenkh').text(invoiceData.customer ? invoiceData.customer.tenkh : 'Không có khách hàng');
    $('#detailNgaylap').text(invoiceData.ngaylap);
    $('#detailNguoilap').text(invoiceData.nguoilap || 'N/A');
    $('#detailGhichu').text(invoiceData.ghichu || 'Không có');

    // 2. Điền các tổng tiền
    $('#detailCongtienhang').text(formatCurrency(invoiceData.congtienhang));
    $('#detailCongchietkhau').text(formatCurrency(invoiceData.congchietkhau));
    $('#detailKhhdathanhtoan').text(formatCurrency(invoiceData.khhdathanhtoan));

    // 3. Xử lý "Còn nợ" và màu sắc
    const connoSpan = $('#detailConno');
    connoSpan.text(formatCurrency(invoiceData.conno));
    if (invoiceData.conno > 0 && invoiceData.trangthai !== 'CANCELLED') {
        connoSpan.removeClass('text-success').addClass('text-danger');
    } else if (invoiceData.conno <= 0 && invoiceData.trangthai !== 'CANCELLED') {
        connoSpan.removeClass('text-danger').addClass('text-success');
    } else { // Trạng thái CANCELLED
        connoSpan.removeClass('text-success text-danger'); // remove any color
    }

    // 4. Xử lý trạng thái và màu sắc
    let statusText = invoiceData.trangthai || 'N/A';
    let statusClass = '';
    switch (invoiceData.trangthai) {
        case 'PAID':
            statusClass = 'text-success fw-bold';
            break;
        case 'CANCELLED':
            statusClass = 'text-muted fst-italic';
            break;
        case 'UNPAID':
        default:
            statusClass = 'text-warning fw-bold';
            break;
    }
    $('#detailTrangthai').html(`<span class="${statusClass}">${statusText}</span>`);

    // 5. Hiển thị thông tin hủy hoặc thay thế nếu có
    if (invoiceData.trangthai === 'CANCELLED') {
        $('.cancel-info').show();
        $('#detailNgayHuy').text(invoiceData.ngayhuy || 'N/A');
        $('#detailNguoiHuy').text(invoiceData.nguoihuy || 'N/A');
    } else {
        $('.cancel-info').hide();
    }

    if (invoiceData.mahd_thaythe) {
        $('.replace-info').show();
        $('#detailMahdThayThe').text(invoiceData.mahd_thaythe);
    } else {
        $('.replace-info').hide();
    }

    // 6. Điền chi tiết sản phẩm vào bảng
    const detailsTableBody = $('#invoiceDetailsTableBody'); // Đảm bảo ID này khớp với HTML của bạn
    detailsTableBody.empty();
    if (invoiceData.details && invoiceData.details.length > 0) {
        invoiceData.details.forEach((item, index) => {
            const row = `
                <tr>
                    <td>${index + 1}</td>
                    <td>${item.product ? item.product.tensp : 'N/A'}</td>
                    <td>${item.donvi || 'N/A'}</td>
                    <td>${item.sl}</td>
                    <td>${formatCurrency(item.dongia)}</td>
                    <td>${item.ck || 0}%</td>
                    <td>${formatCurrency(item.thanhtien)}</td>
                </tr>
            `;
            detailsTableBody.append(row);
        });
    } else {
        detailsTableBody.append('<tr><td colspan="7" class="text-center">Không có chi tiết sản phẩm.</td></tr>');
    }

    // 7. Cập nhật data-attribute và trạng thái hiển thị của các nút hành động trong modal
    $('#editInvoiceBtn').data('mahd', invoiceData.mahd);
    $('#markPaidBtn').data('mahd', invoiceData.mahd);
    $('#cancelInvoiceModalBtn').data('mahd', invoiceData.mahd);
    $('#printInvoiceBtn').attr('onclick', `window.open('/invoices/print-preview/${invoiceData.mahd}', '_blank')`);

    // Ẩn/hiện các nút tùy thuộc vào trạng thái hóa đơn
    if (invoiceData.trangthai === 'CANCELLED' || invoiceData.trangthai === 'PAID') {
        $('#editInvoiceBtn, #markPaidBtn, #cancelInvoiceModalBtn').hide();
    } else {
        $('#editInvoiceBtn, #markPaidBtn, #cancelInvoiceModalBtn').show();
    }

    // 8. Mở modal (đảm bảo ID này khớp với HTML của modal của bạn)
    const invoiceDetailModalElement = document.getElementById('invoiceDetailModal');
    if (invoiceDetailModalElement) {
        const invoiceDetailModal = new bootstrap.Modal(invoiceDetailModalElement);
        invoiceDetailModal.show();
    } else {
        console.error("Modal with ID 'invoiceDetailModal' not found.");
    }
}
function printInvoiceDetails() {
    // Debug: Kiểm tra xem currentInvoiceDetails có dữ liệu không
    console.log("Debug: currentInvoiceDetails on print click:", currentInvoiceDetails);

    if (!currentInvoiceDetails || !currentInvoiceDetails.mahd) {
        Swal.fire('Lỗi', 'Không có hóa đơn được chọn để in. Vui lòng chọn hóa đơn trước.', 'error');
        console.error("Error: currentInvoiceDetails or mahd is missing for print.");
        return;
    }

    const mahd = currentInvoiceDetails.mahd;
    const printUrl = `/invoices/print-preview/${mahd}`;

    // Debug: In ra URL sẽ được sử dụng để mở cửa sổ in
    console.log("Debug: Generated printUrl:", printUrl);
    console.log("Debug: Attempting to open print window...");

    // Mở cửa sổ mới
    const printWindow = window.open(printUrl, '_blank');

    // Kiểm tra xem cửa sổ có thực sự được mở không và không bị trình duyệt chặn
    if (!printWindow || printWindow.closed || typeof printWindow.closed == 'undefined') {
        console.error("Debug: Failed to open print window. Likely blocked by pop-up blocker or browser settings.");
        Swal.fire({
            icon: 'warning',
            title: 'Cảnh báo!',
            text: 'Trình duyệt của bạn có thể đã chặn cửa sổ in. Vui lòng cho phép pop-up cho trang này và thử lại.',
            confirmButtonText: 'Đã hiểu'
        });
    } else {
        // Nếu cửa sổ mở thành công, thêm event listener để in khi trang load xong
        printWindow.onload = function () {
            console.log("Debug: Print window loaded.");
            printWindow.focus(); // Đảm bảo cửa sổ in được focus
            printWindow.print(); // Kích hoạt lệnh in
            // Optional: Đóng cửa sổ sau khi in nếu muốn (hãy cẩn thận với việc này, người dùng có thể muốn xem trước)
            // printWindow.onafterprint = function() {
            //     printWindow.close();
            // };
        };
        // Xử lý trường hợp nếu trình duyệt không hỗ trợ onload cho cửa sổ pop-up hoặc load quá nhanh
        // Một số trình duyệt tự động print nếu target là _blank và content là print-friendly
        // Tuy nhiên, việc có onload vẫn là best practice.
    }
}
function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            let date = new Date(dateString);
            // If the initial parse results in an invalid date, try parsing as ISO string
            if (isNaN(date.getTime())) {
                date = new Date(dateString.replace(' ', 'T'));
            }
            
            if (!isNaN(date.getTime())) {
                // Explicitly format to include hour, minute, second
                const options = {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false // Use 24-hour format
                };
                return date.toLocaleString('vi-VN', options);
            }
            return 'Không hợp lệ';
        } catch (e) {
            console.error("Lỗi định dạng ngày:", dateString, e);
            return 'Lỗi định dạng';
        }
    }