import pygame
import random

# --- 基础配置 ---
WIDTH = 480       # 屏幕宽度
HEIGHT = 600      # 屏幕高度
FPS = 60          # 帧率 

# 颜色定义 (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 初始化 Pygame
pygame.init()
pygame.mixer.init() # 初始化音效（虽然本例未加声音，但保留习惯）
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("简易雷霆战机 - Python版")
clock = pygame.time.Clock()

# --- 类定义 ---

class Player(pygame.sprite.Sprite):
    """玩家飞机"""
    def __init__(self):
        super().__init__()
        # 使用绿色三角形代表飞机
        self.image = pygame.Surface((50, 40))
        # self.image.fill(BLACK) # 背景透明处理需更复杂，这里用黑色填充
        self.image.set_colorkey(BLACK) 
        # 画一个三角形
        pygame.draw.polygon(self.image, GREEN, [(0, 40), (25, 0), (50, 40)])
        
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0
        self.speedy = 0

    def update(self):
        # 键盘控制
        self.speedx = 0
        self.speedy = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -8
        if keystate[pygame.K_RIGHT]:
            self.speedx = 8
        if keystate[pygame.K_UP]:
            self.speedy = -8
        if keystate[pygame.K_DOWN]:
            self.speedy = 8

        # 移动
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        # 边界检测（不让飞机飞出屏幕）
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT
        if self.rect.top < 0:
            self.rect.top = 0

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)

class Enemy(pygame.sprite.Sprite):
    """敌机"""
    def __init__(self):
        super().__init__()
        # 红色矩形代表敌机
        self.image = pygame.Surface((30, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        # 随机出现在顶部
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        # 随机速度
        self.speedy = random.randrange(1, 8)
        self.speedx = random.randrange(-3, 3)

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        # 如果飞出底部，重置到顶部
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)

class Bullet(pygame.sprite.Sprite):
    """子弹"""
    def __init__(self, x, y):
        super().__init__()
        # 黄色小长条
        self.image = pygame.Surface((10, 20))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        # 飞出屏幕上方则销毁
        if self.rect.bottom < 0:
            self.kill()

# 绘制分数的函数
font_name = pygame.font.match_font('arial')
def draw_text(surf, text, size, x, y):
    font = pygame.font.Font(font_name, size)
    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

# --- 游戏主循环 ---

# 创建精灵组
all_sprites = pygame.sprite.Group()
mobs = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# 创建玩家
player = Player()
all_sprites.add(player)

# 创建初始敌机 (8个)
for i in range(8):
    m = Enemy()
    all_sprites.add(m)
    mobs.add(m)

score = 0
running = True

while running:
    # 1. 保持循环以正确的速度运行
    clock.tick(FPS)

    # 2. 处理事件 (键盘、鼠标、关闭窗口)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # 3. 更新所有精灵状态
    all_sprites.update()

    # 4. 碰撞检测 - 子弹击中敌机
    # groupcollide(组1, 组2, 删除组1成员?, 删除组2成员?)
    hits = pygame.sprite.groupcollide(mobs, bullets, True, True)
    for hit in hits:
        score += 10  # 加分
        m = Enemy()  # 补充新的敌机
        all_sprites.add(m)
        mobs.add(m)

    # 5. 碰撞检测 - 敌机撞到玩家
    hits = pygame.sprite.spritecollide(player, mobs, False)
    if hits:
        running = False # 游戏结束

    # 6. 绘制 / 渲染
    screen.fill(BLACK) # 清屏黑色
    all_sprites.draw(screen) # 绘制所有角色
    draw_text(screen, str(score), 18, WIDTH / 2, 10) # 显示分数

    # 翻转显示 (双缓冲)
    pygame.display.flip()

# 退出游戏
print(f"游戏结束！你的最终得分是: {score}")
pygame.quit()