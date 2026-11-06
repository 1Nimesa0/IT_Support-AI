---
sop_id: "SOP-WIFI-001"
title: "Wi-Fi Connected but No Internet Access"
category: "Network"
symptoms:
  - "no internet access"
  - "yellow exclamation mark"
  - "connected, no internet"
  - "mạng chấm than vàng"
  - "kết nối wifi nhưng không vào được mạng"
  - "không vào được web"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Kiểm tra IP address và Default Gateway bằng lệnh ipconfig."
    instruction_spoken: "Trước tiên, bạn mở cửa sổ Run bằng tổ hợp phím Windows cộng R, gõ cmd và nhập lệnh ipconfig rồi nhấn Enter giúp mình nhé."
    expected_confirmation:
      - "đã thấy ip"
      - "hiện ra địa chỉ rồi"
      - "đã gõ xong"
      - "xong rồi"
      - "có ip rồi"
    fallback_instruction: "Nếu bạn không ấn được phím tắt, hãy nhấn chuột phải vào nút Start ở góc dưới màn hình và chọn Terminal hoặc Command Prompt."
    shortcut: "Win + R -> cmd -> ipconfig"
  - step_id: 2
    action: "Kiểm tra kết nối mạng qua IP với lệnh ping 8.8.8.8."
    instruction_spoken: "Bây giờ bạn gõ tiếp lệnh: ping 8 chấm 8 chấm 8 chấm 8 rồi xem màn hình có báo dòng Reply from hay Request timed out nhé."
    expected_confirmation:
      - "reply from"
      - "có reply"
      - "thấy reply rồi"
      - "chạy tốt"
      - "có phản hồi"
    fallback_instruction: "Nếu thấy Request timed out, bạn thử ngắt kết nối Wi-Fi rồi kết nối lại xem router có cấp lại IP không nhé."
    shortcut: "ping 8.8.8.8"
  - step_id: 3
    action: "Xóa DNS cache và làm mới cấu hình mạng bằng ipconfig /flushdns và /renew."
    instruction_spoken: "Bạn gõ lệnh: ipconfig xẹc flushdns, sau đó gõ tiếp ipconfig xẹc renew để làm mới địa chỉ mạng nhé."
    expected_confirmation:
      - "successfully flushed"
      - "đã làm mới xong"
      - "vào được mạng rồi"
      - "lướt web bình thường rồi"
    fallback_instruction: "Nếu vẫn chưa vào được mạng, bạn hãy thử khởi động lại card mạng Wi-Fi trong Network Connections hoặc liên hệ IT trực tiếp để kiểm tra Access Point."
    shortcut: "ipconfig /flushdns && ipconfig /renew"
---
# Hướng Dẫn Xử Lý Lỗi Wi-Fi Kết Nối Nhưng Không Có Internet

## Mô tả tổng quan
Quy trình chuẩn xử lý sự cố thiết bị đã kết nối vào mạng Wi-Fi văn phòng hoặc gia đình nhưng biểu tượng mạng hiển thị "No Internet" (chấm than vàng) hoặc không mở được các trang web.

## Các bước thực hiện
1. **Kiểm tra IP và Gateway**: Xác định máy tính có nhận được IP hợp lệ từ DHCP server (dải 192.168.x.x hoặc 10.x.x.x) hay đang bị gán địa chỉ APIPA (169.254.x.x).
2. **Kiểm tra kết nối ICMP ra Internet**: Ping DNS công cộng của Google (8.8.8.8) để phân biệt sự cố tầng định tuyến (Routing) hay sự cố phân giải tên miền (DNS).
3. **Làm mới bộ nhớ đệm DNS & DHCP Lease**: Giải phóng và tái cấp phát địa chỉ IP qua lệnh `ipconfig /release` và `ipconfig /renew`.
