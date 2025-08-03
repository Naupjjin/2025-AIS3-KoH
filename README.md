# Mortis GO\!\!!!! 
> Author: naup96321、Itiscaleb、Curious

[簡報](https://docs.google.com/presentation/d/1nrtJzzr6muogeTYb40M8NPEScsHizw5zIWlP42dyWSo/edit?usp=sharing)
## Description
小睦因為太久沒上學所以跟不上進度，只好分裂出多重人格找小祥補進度
小祥會給小睦的不同人格題目，解出來就能獲得分數
或是也可以選擇幹掉其他的人格，在多重人格大逃殺中吃雞

## 玩法

隊伍通過上傳 assembly (詳見指令集) 來遊玩遊戲，1 round 遊戲共有 200 turn，每 turn 都會去執行同一段 assembly，並回傳一個指令 (詳見指令)
每五分鐘為 1 round，這裡稱作 active，並且 round 與 round 中間會有時長不一的 pending
若無上傳新腳本，則會沿用之前提交的最新腳本
模擬後會根據遊戲分數進行排名轉換成實際分數 (詳見計分方式)

ex:
round 31 active 時上傳腳本 --> round 31 pending 等待進入 round 32 --> round 32 active 模擬該 round 前上傳的最新腳本並更新分數 (模擬時間長短不一，請耐心等候) 


## 計分方式

### Scoreboard 分數
每 round 會去跑玩家上傳的 assembly，並統計該輪遊戲獲得的分數，排名後會轉換成會記錄在 scoreboard 上的分數
轉換方是如下:

| Rank | Score (scorebboard) |
|-|-|
| 1| 30 |
| 2| 20 |
| 3| 15 |
| 4、5| 8 |
| 6、7| 3 |
| 8、9、10| 1 |

若該 round 沒有拿到任何分數以 0 分計算
同分狀況則如下轉換:

team 8、4 遊戲分數 52 分
team 9 遊戲分數 48 分
team 1、2、7 遊戲分數 6 分

則
team 8、4 並列第一名拿到 30 分
跳過第二名
team 9 第三名拿到 20 分
team 1、2、7 第四名拿到 8 分

### 遊戲分數
通過編寫 assembly，可以操控玩家並互動地圖上的物件
可以通過以下方式來獲取分數

- 移動(1 分): 若該 turn 有移動玩家 (本體、分身)
- 殺人:
	- 擊殺本體 (70 分): 本體共有 3 滴血，若你成功擊殺別支隊伍本體可得分
	- 擊殺分身 (40 分): 分身共有 2 滴血，若你成功擊殺別支隊伍分身可得分
- 箱子(藍色章魚): 通過互動可以拿到任務，會將任務相關資訊放置在記憶體上，之後將任務需求放置到對應記憶體上，再次互動，若正確即可得分，共有以下幾種任務，分別有不同分數
	- 1 反轉數字 (~~30 分~~60分): 7 個參數，7 個答案 (ex: 1234567 (七個) 反轉成 7654321)
	- 2 排序 (~~40 分~~80分): 7 個參數，7 個答案 (ex: 2、5、4、1、6、3 排序成 1、2、3、4、5、6)
	- 3 RSA 解密 (~~50 分~~100分): 4 個參數 (p、q、e、c)，1 個答案 (m)
	- 4 ECC 點加法 (~~60 分~~120分): 7 個參數(a、b、p、P_x、P_y、Q_x、Q_y)，2 個答案 (R_X、R_y)，給定曲線 y\^2=x\^3+ax+b (mod p)，計算曲線上兩個 P、Q 之 P+Q = R 為多少

buf[50] 題目編號
buf[51] ~ buf[57] 按順序放置參數及答案

## 記憶體
玩家有 100 格可以存 unsigned int 的記憶體
- buf[0] ~ buf[49] 玩家與分身共用，會繼承
- buf[50] ~ buf[57] 玩家及分身自己用，會繼承
- buf[58] ~ buf[99] 玩家及分身自己用，不會繼承

## 地圖
每 5 round 會刷新地圖 (ex: 1-5 round 為第一張、6-10 為第二張，以此類推)
當模擬完畢後，可以在 `game` 的地方看到該輪模擬結果
- 按 `1` 可以追蹤一個玩家
- 按 `2` 回到全地圖
- 按 `+` 可以看到下一 turn (本地測試提供)
- 按 `-` 可以看到上一 turn (本地測試提供)
- 按 `shift` 和 `+` 可以加速進行 (本地測試提供)

地圖的每一格可能會是 path = 0、wall = 1、chest = 2、player = 4，並且 or 起來，
ex: 若 buf[3] = 0, buf[4] = 0，且在 map[0][0] 的位置同時存在玩家跟箱子
則 load_map 0 3 4 的結果會是 2 | 4 = 6





## 指令
玩家可以透過不同的 Instruction 來操控記憶體或是控制程式流程
並在最後透過 ret 回傳不同的數字來控制 Mortis

| number | 指令 | 描述 | 
|-|-| - |
| 0| stop | 無動作 |
| 1| up | 往上走一格 |
| 2| down | 往下走一格 |
| 3| left | 往左走一格 |
| 4| right | 往右走一格 |
| 5| interact | 跟周圍 8 格寶箱互動 (不包含自身所在位置) |
| 6| attack | 攻擊周圍 8 格 (不包含自身所在位置) |
| 7| fork | 在原地分身 |

備註: assembly 每 turn timeout 上限為 250 ms，若該 turn timeout 則會直接回傳 0

## 角色
玩家本體會有 3 滴血，而分身會有 2 滴血
本體死後會在隨機位置重生，分身則會消失


## fork
當執行 fork 時，玩家可以在原地產生分身
基礎消耗是 70 
一個玩家可以最多有 3 個分身，並且每次 fork 時，所需的分數就會變成 1.2 倍，
fork 會執行跟一開始的角色一樣的 assembly

## 指令集
- memory: 以 memX 表示，例如 mem0, mem1，撰寫時使用 index，ex: `1`、`83`
- constant: 以前綴 `#` 標示，ex: `#1`、`#83`
- label: 任意 label 名稱，並在結尾加上 `:`，ex: `avemujica:`
- 可以使用 `//` 來當註解 (15:53 update)

| 指令 | 說明 |
|------|------|
| `mov <mem1> <mem2>` | `mem1 = mem2` |
| `mov <mem1> #<constant>` | `mem1 = constant` |
| `movi <mem1> <mem2>` |`*mem1 = *mem2` |
| `add <mem1> <mem2>` | `mem1 += mem2` |
| `add <mem1> #<constant>` | `mem1 += constant` |
| `shr <mem1> <mem2>` | `mem1 >>= mem2` |
| `shr <mem1> #<constant>` | `mem1 >>= constant` |
| `shl <mem1> <mem2>` | `mem1 <<= mem2` |
| `shl <mem1> #<constant>` | `mem1 <<= constant` |
| `mul <mem1> <mem2>` | `mem1 *= mem2` |
| `mul <mem1> #<constant>` | `mem1 *= constant` |
| `div <mem1> <mem2>` | `mem1 /= mem2` |
| `div <mem1> #<constant>` | `mem1 /= constant` |
| `je <mem1> <mem2> <label>` | 若 `mem1 == mem2` 則跳轉至 `<label>` |
| `je <mem1> #<constant> <label>` | 若 `mem1 == constant` 則跳轉至 `<label>` |
| `jg <mem1> <mem2> <label>` | 若 `mem1 > mem2` 則跳轉至 `<label>` |
| `jg <mem1> #<constant> <label>` | 若 `mem1 > constant` 則跳轉至 `<label>` |
| `inc <mem1>` | `mem1++` |
| `dec <mem1>` | `mem1--` |
| `and <mem1> <mem2>` | `mem1 &= mem2` |
| `and <mem1> #<constant>` | `mem1 &= constant` |
| `or <mem1> <mem2>` | `mem1 \|= mem2` |
| `or <mem1> #<constant>` | `mem1 \|= constant` |
| `ng <mem1>` | `mem1 = ~mem1` |
| `ret <mem1>` | 結束並返回 `mem1` 的值 (返回值就是指令) |
| `ret #<constant>` | 結束並返回常數 (返回值就是指令) |
| `load_score <mem1>` | 將當前分數載入 `mem1` |
| `load_loc <mem1>` | 載入當前 (x,y) 的至 `mem1[0]` 及 `mem1[1]`  |
| `load_map <mem1> <mem2> <mem3>` | 將 map(mem2,mem3) 載入 mem1|
| `get_id <mem1>` | 將角色 ID 載入 `mem1`，如果是 0 就是分身 |
| `locate_nearest_k_chest <mem1> <mem2>` | 從 0 開始，將距離第 `mem2` 個最近寶箱的座標 `(x,y)` 存入 `mem1[0]` 與 `mem1[1]` |
| `locate_nearest_k_chest <mem1> #<constant>` | 從 0 開始，將距離第 `constant` 個最近寶箱的座標 `(x,y)` 存入 `mem1[0]` 與 `mem1[1]`，不會找到自己的角色(本體跟分身) |
| `locate_nearest_k_character <mem1> <mem2>` | 從 0 開始，將距離第 `mem2` 個最近角色的資訊存入 `mem1[0..2]`，分別是 `is_fork`、  `(x,y)`，不會找到自己的角色(本體跟分身) |
| `locate_nearest_k_character <mem1> #<constant>` | 從 0 開始，將距離第 `constant` 個最近角色的資訊存入 `mem1[0..2]`，分別是 `is_fork`、  `(x,y)` |

## 本地測試
[Local Test file](https://github.com/Naupjjin/2025-KoH-dist)
```
├── app.py
├── Makefile
├── maps
    └── gen_map.py
├── simulator.py
├── static
├── templates
└── vm
    ├── vm.cpp
    └── vm.h
```

提供可以進行本地測試的檔案，可以將 `app.py` 跑起來
備註1 : 在跑網頁前，需先 `make` 將 `vm` 編譯好
備註2 : 通過 `maps/gen_map.py` 產生的地圖可以作為本地測試用，但會產生封閉區域，不過這邊確保遠端的地圖沒有封閉區域 
