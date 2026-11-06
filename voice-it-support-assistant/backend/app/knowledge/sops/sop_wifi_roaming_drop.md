---
sop_id: "SOP-WIFI-003"
title: "Frequent Wi-Fi Disconnections and Roaming Drops"
category: "Network"
symptoms:
  - "wifi chập chờn"
  - "liên tục bị ngắt kết nối"
  - "đi lại giữa các phòng bị mất mạng"
  - "roaming drop"
  - "frequent wifi disconnect"
prerequisites:
  device_type: ["Windows", "macOS"]
steps:
  - step_id: 1
    action: "Kiểm tra và điều chỉnh thuộc tính Roaming Aggressiveness của card mạng Wi-Fi."
    instruction_spoken: "Bạn mở Device Manager bằng cách bấm chuột phải vào Start chọn Device Manager, tìm mục Network adapters và nhấn đúp vào card Wi-Fi nhé."
    expected_confirmation:
      - "đã mở device manager"
      - "thấy card wifi rồi"
      - "đã nhấn đúp"
      - "xong rồi"
    fallback_instruction: "Bạn có thể bấm tổ hợp phím Windows cộng X rồi ấn chữ M để mở nhanh Device Manager."
    shortcut: "Win + X -> Device Manager -> Network adapters"
  - step_id: 2
    action: "Chuyển sang tab Advanced và đặt Roaming Aggressiveness về mức Medium hoặc Low."
    instruction_spoken: "Trong cửa sổ hiện ra, bạn chuyển sang thẻ Advanced, tìm dòng Roaming Aggressiveness và đổi giá trị thành Medium giúp mình nhé."
    expected_confirmation:
      - "đã đổi sang medium rồi"
      - "đã chọn medium"
      - "xong rồi"
    fallback_instruction: "Nếu card mạng là Intel, mục này có tên Roaming Aggressiveness; nếu là Realtek bạn tìm mục Roaming Sensitivity."
    shortcut: "Tab Advanced -> Roaming Aggressiveness = 3. Medium"
  - step_id: 3
    action: "Tắt tính năng tiết kiệm điện cho card mạng."
    instruction_spoken: "Bạn chuyển sang thẻ Power Management, bỏ dấu tích ở dòng Allow the computer to turn off this device to save power rồi bấm OK nhé."
    expected_confirmation:
      - "đã bỏ tích rồi"
      - "đã bấm ok"
      - "xong rồi"
      - "ổn định rồi"
    fallback_instruction: "Sau khi bấm OK, bạn khởi động lại kết nối Wi-Fi bằng cách bật tắt chế độ máy bay Airplane Mode."
    shortcut: "Power Management -> Uncheck 'Allow computer to turn off'"
---
# Xử Lý Sự Cố Wi-Fi Chập Chờn Khi Di Chuyển Giữa Các Vùng Phủ Sóng (Roaming Drop)
