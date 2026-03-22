# TODOS

## VN Realtime Quotes (V2)
- **What:** Implement `VnstocksFetcher.get_realtime_quote()` cho VN stocks
- **Why:** V1 chỉ có daily data. Pipeline trả `None` cho realtime → report thiếu giá hiện tại, tên stock, derived metrics
- **Pros:** Full UX parity với CN/US/HK stocks trong reports
- **Cons:** Cần xử lý VN trading hours (GMT+7, 9:00-11:30 & 13:00-15:00), rate limit khác biệt
- **Context:** vnstock Quote API có `quote.intraday()`. VN market có 2 phiên giao dịch/ngày. Rate limit Guest=20/phút, Community=60/phút
- **Depends on:** V1 VN stocks integration PR phải merge trước
- **Added:** 2026-03-22 (eng review)

## VN Stock Name Mapping
- **What:** Thêm VN stock names vào `STOCK_NAME_MAP` hoặc fetch từ vnstock API
- **Why:** Reports hiển thị mã (FPT) thay vì tên công ty (FPT Corporation). UX kém
- **Pros:** Dễ đọc report, consistent với CN/US/HK hiển thị tên
- **Cons:** Cần maintain static mapping hoặc thêm API call khi init
- **Context:** vnstock có `listing.all_symbols()` trả về danh sách mã + tên đầy đủ
- **Depends on:** V1 VN stocks integration PR phải merge trước
- **Added:** 2026-03-22 (eng review)
