from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func, or_
from typing import Optional, List
from datetime import date, timedelta
from pydantic import BaseModel, ConfigDict # <-- Đảm bảo dòng này có BaseModel và ConfigDict

from ..database import get_session
from ..models import Invoice, InvoiceDetail, Customer #, Product

router = APIRouter(prefix="/reports", tags=["Reports"])

# Pydantic models for report data
class CustomerReportDetail(BaseModel): # <-- CHẮC CHẮN LÀ BASEMODEL, KHÔNG PHẢI CUSTOMER
    makh: int
    tenkh: str
    diachi_sdt: Optional[str] = None
    ghichu: Optional[str] = None

    # conno của khách hàng trong bảng Customer (công nợ tích lũy)
    conno_from_customer_table: float = 0.0 # Đổi tên để tránh nhầm lẫn

    total_goods_amount: float = 0.0
    total_discount_amount: float = 0.0
    total_invoice_amount: float = 0.0 # congtienhang - congchietkhau
    total_paid_amount: float = 0.0 # khdathanhtoan của các hóa đơn trong kỳ
    current_debt_in_period: float = 0.0 # conno của các hóa đơn trong kỳ

    model_config = ConfigDict(from_attributes=True) # Dùng cho Pydantic v2
    # Nếu bạn dùng Pydantic v1, dùng:
    # class Config:
    #     from_attributes = True

class ReportSummary(BaseModel): # <-- CHẮC CHẮN LÀ BASEMODEL
    total_revenue: float
    total_paid_amount: float
    total_customer_debt: float
    customer_details: List[CustomerReportDetail]

    model_config = ConfigDict(from_attributes=True) # Dùng cho Pydantic v2
    # Nếu bạn dùng Pydantic v1, dùng:
    # class Config:
    #     from_attributes = True

# Endpoint để lấy tổng công nợ từ tất cả khách hàng
@router.get("/total-debt", response_model=dict, summary="Get total outstanding debt from all customers")
def get_total_debt(db: Session = Depends(get_session)):
    try:
        total_debt_sum = db.exec(select(func.sum(Customer.conno))).first()
        return {"total_debt": total_debt_sum if total_debt_sum is not None else 0.0}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching total debt: {e}")

# Endpoint báo cáo tổng hợp theo thời gian và chi tiết theo khách hàng
@router.get("/summary", response_model=ReportSummary, summary="Get sales and debt report summary")
def get_report_summary(
    year: int = Query(..., description="Năm cần báo cáo"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Tháng cần báo cáo (nếu có)"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quý cần báo cáo (nếu có)"),
    db: Session = Depends(get_session)
):
    try:
        # Xây dựng điều kiện lọc theo ngày
        start_date = None
        end_date = None

        if month:
            if not (1 <= month <= 12):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tháng không hợp lệ.")
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        elif quarter:
            if not (1 <= quarter <= 4):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quý không hợp lệ.")
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            start_date = date(year, start_month, 1)
            if end_month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, end_month + 1, 1) - timedelta(days=1)
        else: # Yearly report
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)

        print(f"Generating report from {start_date} to {end_date}")

        # Tính tổng doanh thu, đã thanh toán, công nợ cho toàn bộ kỳ báo cáo
        total_revenue_query = select(
            func.sum(Invoice.congtienhang - Invoice.congchietkhau).label('total_revenue'),
            func.sum(Invoice.khhdathanhtoan).label('total_paid_amount'),
            func.sum(Invoice.conno).label('total_outstanding_debt')
        ).where(
            Invoice.ngaylap >= start_date,
            Invoice.ngaylap <= end_date,
            Invoice.trangthai != "CANCELLED" # Không tính hóa đơn đã hủy
        )
        summary_row = db.exec(total_revenue_query).first()

        total_revenue = summary_row.total_revenue if summary_row and summary_row.total_revenue is not None else 0.0
        total_paid_amount = summary_row.total_paid_amount if summary_row and summary_row.total_paid_amount is not None else 0.0
        total_outstanding_debt = summary_row.total_outstanding_debt if summary_row and summary_row.total_outstanding_debt is not None else 0.0
        
        # Lấy thông tin chi tiết từng khách hàng trong kỳ
        # Lấy tất cả khách hàng
        customers = db.exec(select(Customer)).all()
        customer_details = []

        for customer in customers:
            customer_invoice_query = select(
                func.sum(Invoice.congtienhang).label('total_goods_amount'),
                func.sum(Invoice.congchietkhau).label('total_discount_amount'),
                func.sum(Invoice.congtienhang - Invoice.congchietkhau).label('total_invoice_amount'),
                func.sum(Invoice.khhdathanhtoan).label('total_paid_amount'),
                func.sum(Invoice.conno).label('current_debt') # conno của các hóa đơn của KH trong kỳ
            ).where(
                Invoice.makh == customer.makh,
                Invoice.ngaylap >= start_date,
                Invoice.ngaylap <= end_date,
                Invoice.trangthai != "CANCELLED"
            )
            customer_summary = db.exec(customer_invoice_query).first()

            if customer_summary and (customer_summary.total_goods_amount is not None or customer_summary.total_discount_amount is not None or customer_summary.total_invoice_amount is not None or customer_summary.total_paid_amount is not None or customer_summary.current_debt is not None):
                 # Chỉ thêm vào danh sách nếu có hóa đơn trong kỳ hoặc có công nợ phát sinh trong kỳ
                customer_detail = CustomerReportDetail(
                    makh=customer.makh,
                    tenkh=customer.tenkh,
                    diachi_sdt=customer.diachi_sdt,
                    ghichu=customer.ghichu,
                    conno=customer.conno, # Đây là tổng công nợ của khách hàng (hiện tại), giữ nguyên
                    total_goods_amount=customer_summary.total_goods_amount if customer_summary.total_goods_amount is not None else 0.0,
                    total_discount_amount=customer_summary.total_discount_amount if customer_summary.total_discount_amount is not None else 0.0,
                    total_invoice_amount=customer_summary.total_invoice_amount if customer_summary.total_invoice_amount is not None else 0.0,
                    total_paid_amount=customer_summary.total_paid_amount if customer_summary.total_paid_amount is not None else 0.0,
                    current_debt=customer_summary.current_debt if customer_summary.current_debt is not None else 0.0 # conno của các hóa đơn của KH trong kỳ
                )
                customer_details.append(customer_detail)
            # else:
            #     # Nếu không có hóa đơn trong kỳ, nhưng khách hàng có công nợ từ các kỳ khác, vẫn có thể muốn hiển thị
            #     # Tùy thuộc vào yêu cầu nghiệp vụ, bạn có thể thêm khách hàng có conno > 0 vào đây
            #     if customer.conno > 0:
            #         customer_detail = CustomerReportDetail(
            #             makh=customer.makh,
            #             tenkh=customer.tenkh,
            #             diachi_sdt=customer.diachi_sdt,
            #             ghichu=customer.ghichu,
            #             conno=customer.conno,
            #             total_goods_amount=0.0,
            #             total_discount_amount=0.0,
            #             total_invoice_amount=0.0,
            #             total_paid_amount=0.0,
            #             current_debt=customer.conno # Lấy công nợ hiện tại của khách hàng
            #         )
            #         customer_details.append(customer_detail)


        return ReportSummary(
            total_revenue=total_revenue,
            total_paid_amount=total_paid_amount,
            total_customer_debt=total_outstanding_debt,
            customer_details=customer_details
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Đã xảy ra lỗi khi tạo báo cáo: {e}")