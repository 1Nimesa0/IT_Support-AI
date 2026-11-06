---
sop_id: "SOP-AUTH-002"
title: "Multi-Factor Authentication (MFA) OTP Desynchronization"
category: "Authentication"
symptoms:
  - "mã otp không đúng"
  - "mfa invalid code"
  - "microsoft authenticator mã sai"
  - "otp desync"
  - "nhập đúng mã otp nhưng báo lỗi"
prerequisites:
  device_type: ["Mobile", "Windows", "macOS"]
steps:
  - step_id: 1
    action: "Đồng bộ lại đồng hồ thời gian trên điện thoại chứa ứng dụng Authenticator."
    instruction_spoken: "Lỗi này thường do giờ điện thoại bị lệch vài giây. Bạn vào Cài đặt điện thoại, chọn Ngày và Giờ, rồi bật Tự động cập nhật giờ mạng nhé."
    expected_confirmation:
      - "đã bật giờ tự động"
      - "đã chỉnh lại giờ"
      - "xong rồi"
      - "đã đồng bộ giờ"
    fallback_instruction: "Trên Android, bạn có thể mở Google Authenticator, vào dấu 3 chấm góc phải, chọn Cài đặt -> Chỉnh sửa giờ cho mã xác minh -> Đồng bộ ngay."
    shortcut: "Phone Settings -> Date & Time -> Set Automatically"
  - step_id: 2
    action: "Chờ chuyển sang chu kỳ mã OTP tiếp theo (vòng tròn đếm ngược)."
    instruction_spoken: "Sau khi cập nhật giờ, bạn đợi vòng tròn đếm ngược trên app chạy hết và nhập mã 6 số mới toanh vừa xuất hiện nhé."
    expected_confirmation:
      - "đã nhập mã mới"
      - "vào được rồi"
      - "nhận mã rồi"
      - "thành công rồi"
    fallback_instruction: "Nếu vẫn báo mã sai, bạn bấm vào liên kết 'Đăng nhập bằng cách khác' trên màn hình đăng nhập để nhận mã qua tin nhắn SMS hoặc cuộc gọi."
    shortcut: "Wait 30s for fresh OTP"
  - step_id: 3
    action: "Kích hoạt phương thức xác thực dự phòng hoặc cấp Temporary Access Pass (TAP)."
    instruction_spoken: "Nếu điện thoại của bạn bị đổi máy hoặc mất quyền truy cập app, IT sẽ tạo mã đăng nhập tạm thời TAP để bạn cấu hình lại thiết bị nhé."
    expected_confirmation:
      - "đã nhận mã tạm thời"
      - "đã quét lại mã qr"
      - "xong rồi"
    fallback_instruction: "Vui lòng liên hệ quản trị viên IT qua hotline nội bộ nhánh 101 để được cấp TAP có hiệu lực trong 8 giờ."
    shortcut: "IT Admin -> Issue TAP (Temporary Access Pass)"
---
# Xử Lý Sự Cố Lệch Mã Xác Thực Đa Yếu Tố (MFA OTP Desynchronization)
