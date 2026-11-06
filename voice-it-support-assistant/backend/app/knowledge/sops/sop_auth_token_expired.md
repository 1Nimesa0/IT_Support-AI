---
sop_id: "SOP-AUTH-003"
title: "Single Sign-On (SSO) OAuth2 Token Expired or Refresh Failure"
category: "Authentication"
symptoms:
  - "phiên đăng nhập hết hạn"
  - "token expired"
  - "sso session expired"
  - "refresh token failed"
  - "lỗi xác thực đăng nhập 1 lần sso"
  - "liên tục bắt đăng nhập lại"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Xóa cookies và session cache của dịch vụ SSO trên trình duyệt."
    instruction_spoken: "Bạn nhấn tổ hợp phím Ctrl cộng Shift cộng Delete trên trình duyệt, chọn xóa Cookies và Cached images trong 24 giờ qua rồi bấm Xóa nhé."
    expected_confirmation:
      - "đã xóa cookie rồi"
      - "đã xóa cache"
      - "xong rồi"
    fallback_instruction: "Bạn có thể thử mở một cửa sổ ẩn danh mới bằng Ctrl cộng Shift cộng N để kiểm tra xem có đăng nhập được không."
    shortcut: "Ctrl + Shift + Delete -> Clear Cookies & Cache"
  - step_id: 2
    action: "Đăng xuất hoàn toàn khỏi cổng SSO trung tâm (Microsoft 365 / Google Workspace)."
    instruction_spoken: "Bạn truy cập vào trang login.microsoftonline.com hoặc accounts.google.com và bấm Đăng xuất khỏi tất cả tài khoản nhé."
    expected_confirmation:
      - "đã đăng xuất hết rồi"
      - "đã sign out"
      - "xong rồi"
    fallback_instruction: "Nếu trình duyệt tự động đăng nhập lại bằng tài khoản cũ, hãy đóng toàn bộ cửa sổ trình duyệt và mở lại."
    shortcut: "Visit https://portal.office.com -> Sign Out"
  - step_id: 3
    action: "Đăng nhập lại và cấp mới Refresh Token."
    instruction_spoken: "Bây giờ bạn truy cập lại vào ứng dụng của công ty, nhập thông tin đăng nhập và xác thực MFA để nhận phiên làm việc mới nhé."
    expected_confirmation:
      - "đã vào được ứng dụng"
      - "không bị văng ra nữa"
      - "đăng nhập thành công rồi"
    fallback_instruction: "Nếu vẫn tiếp tục bị văng ra, kiểm tra xem máy tính có cài extension can thiệp cookie như Privacy Badger hay không."
    shortcut: "New Clean SSO Login"
---
# Xử Lý Lỗi Hết Hạn Token Đăng Nhập Một Lần (SSO OAuth2 Token Expired)
