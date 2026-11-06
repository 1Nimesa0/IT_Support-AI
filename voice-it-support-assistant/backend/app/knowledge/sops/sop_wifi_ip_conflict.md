---
sop_id: "SOP-WIFI-004"
title: "IP Address Conflict on Local Network"
category: "Network"
symptoms:
  - "trùng ip"
  - "ip address conflict"
  - "another device is using your ip address"
  - "xung đột địa chỉ ip"
  - "báo lỗi xung đột mạng"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Giải phóng địa chỉ IP hiện tại bằng lệnh ipconfig /release."
    instruction_spoken: "Bạn mở Command Prompt bằng cách bấm Windows cộng R, gõ cmd và nhập ipconfig dấu cách xẹc release rồi nhấn Enter nhé."
    expected_confirmation:
      - "đã release rồi"
      - "đã giải phóng ip"
      - "xong rồi"
      - "ip đã về 0.0.0.0"
    fallback_instruction: "Nhớ có dấu cách giữa ipconfig và dấu gạch chéo nhé: i p c o n f i g cách xẹc release."
    shortcut: "cmd -> ipconfig /release"
  - step_id: 2
    action: "Yêu cầu DHCP Server cấp địa chỉ IP mới bằng ipconfig /renew."
    instruction_spoken: "Tiếp tục bạn gõ lệnh: ipconfig dấu cách xẹc renew rồi đợi vài giây để router cấp IP mới cho máy bạn nhé."
    expected_confirmation:
      - "đã nhận ip mới"
      - "hiện lại ip rồi"
      - "xong rồi"
      - "hết báo trùng rồi"
    fallback_instruction: "Nếu hệ thống bị treo khi renew, hãy rút dây mạng hoặc tắt mở lại Wi-Fi trong 10 giây."
    shortcut: "ipconfig /renew"
  - step_id: 3
    action: "Kiểm tra chế độ gán IP tự động trong IPv4 Adapter Settings."
    instruction_spoken: "Bạn kiểm tra xem card mạng có đang để Obtain an IP address automatically không nhé, đảm bảo không gán IP tĩnh thủ công."
    expected_confirmation:
      - "đang để tự động rồi"
      - "đã bật dhcp"
      - "mạng bình thường rồi"
    fallback_instruction: "Bạn mở ncpa.cpl từ cửa sổ Run, chuột phải vào Wi-Fi chọn Properties, chọn Internet Protocol Version 4 và tích vào ô Obtain an IP address automatically."
    shortcut: "ncpa.cpl -> IPv4 Properties -> Obtain IP automatically"
---
# Hướng Dẫn Giải Quyết Sự Cố Xung Đột Địa Chỉ IP (IP Address Conflict)
