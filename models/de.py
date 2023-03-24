from utils.datasets import *
from utils.utils import *
from models.experimental import attempt_load




def get_model():
    weights = r'weights/Mask_detected.pt'
    device = ("cuda" if (torch.cuda.is_available()) else "cpu")
    model = attempt_load(weights, map_location=device)
    model.to(device).eval()
    return model

def letterbox(img, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True):
    # Resize image to a 32-pixel-multiple rectangle https://github.com/ultralytics/yolov3/issues/232
    shape = img.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better test mAP)
        r = min(r, 1.0)
    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, 64), np.mod(dh, 64)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = new_shape
        ratio = new_shape[0] / shape[1], new_shape[1] / shape[0]  # width, height ratios

    dw /= 2  # divide padding into 2 sides
    dh /= 2
    if shape[::-1] != new_unpad:  # resize
        img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return img, ratio, (dw, dh)

def detect(model, im0s):
    t0 = time.time()
    device = torch.device("cuda" if (torch.cuda.is_available()) else "cpu")
    names = model.names if hasattr(model, 'names') else model.modules.names
    # colors = [[random.randint(0, 255) for _ in range(3)] for _ in range(len(names))] #原作者隨機生成的顏色
    # print(f"共有{colors}這些顏色") # 測試用
    img = letterbox(im0s, new_shape=640)[0]
    img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
    img = np.ascontiguousarray(img)
    img = torch.from_numpy(img).to(device)
    img = img.float()
    img /= 255.0  # 0 - 255 to 0.0 - 1.0
    if img.ndimension() == 3:
        img = img.unsqueeze(0)
    pred = model(img, augment=False)[0]
    pred = non_max_suppression(pred, 0.4, 0.5,
                               fast=True, classes=None, agnostic=False)
    for i, det in enumerate(pred):  # detections per image
        im0 = im0s
        if det is not None and len(det): #len(det)有值的話會是1
            # print(f'det 是 {det}') #測試用
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round() #a[row,col] --> a[start:end, start:end]  reference : https://stackoverflow.com/a/57872912

            # names是模組中預先定義好的類別名稱 cls是名稱的類別(型別值會是<class 'torch.Tensor'>類似1.0這種值) xyxy是tensor值 conf 是信任值 
            for *xyxy, conf, cls in det:
                # print(f'names 是 {names},cls 是 {cls}, xyxy {xyxy}, conf信任值 {conf}, im0是 {im0}') #測試用
                label = '%s%.2f' % (names[int(cls)], conf) #先把cls轉成整數之後從names串列裡面選出名字，這裡會印出像without_mask0.49這樣的字串
                ### 這裡要累加 conf 的值然後算平均判斷這個人是否真的有戴口罩
                print(f'偵測到label --> {label}') #測試用，印出檢測結果
                # im0 = plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=2) #原作者畫框框的函式
                if r'with_mask' in label: #with_mask : 綠色, without_mask : 紅色, mask_weared_incorrect : 顯示黃色
                    im0 = plot_one_box(xyxy, im0, label=label, color=[88, 128, 71], line_thickness=2) #測試用，改框框顏色這裡是BGR不是RGB!!
                elif r'mask_weared_incorrect' in label:
                    im0 = plot_one_box(xyxy, im0, label=label, color=[0, 244, 249], line_thickness=2) #測試用，改框框顏色這裡是BGR不是RGB!!
                else:    
                    im0 = plot_one_box(xyxy, im0, label=label, color=[108, 96, 244], line_thickness=2) #測試用，改框框顏色這裡是BGR不是RGB!!
    print('Done. (%.3fs)' % (time.time() - t0))
    return im0
