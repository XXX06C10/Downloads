import pygame
import random
import math
import os

# --- 基础配置 ---
WIDTH = 480
HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# 初始化 Pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("雷霆战机 EX - 究极进化版")
clock = pygame.time.Clock()

# --- 关键修改：字体处理 ---
# 为了解决中文显示方块的问题，我们需要寻找系统中的中文字体
def get_chinese_font():
    # 常见的跨平台中文字体名称列表
    font_choices = ['simhei', 'microsoftyahei', 'pingfangsc', 'heiti', 'songti']
    for font_name in font_choices:
        path = pygame.font.match_font(font_name)
        if path:
            return path
    # 如果实在找不到，返回None（将使用pygame默认字体，可能仍无法显示中文，但在Windows上通常SimHei都有）
    return None

current_font_path = get_chinese_font()

# --- 辅助绘图函数 ---
def draw_ship_surface(color, type_name):
    """根据类型绘制飞船图像"""
    surf = pygame.Surface((50, 40))
    surf.set_colorkey(BLACK)
    if type_name == "SPEED": # 速度型：细长
        pygame.draw.polygon(surf, color, [(10, 40), (25, 0), (40, 40), (25, 30)])
    elif type_name == "HEAVY": # 重装型：宽大
        pygame.draw.rect(surf, color, (10, 10, 30, 30))
        pygame.draw.polygon(surf, color, [(0, 20), (25, 0), (50, 20)])
    else: # 平衡型
        pygame.draw.polygon(surf, color, [(0, 40), (25, 0), (50, 40)])
        pygame.draw.circle(surf, RED, (25, 20), 5)
    return surf

def draw_text(surf, text, size, x, y, color=WHITE):
    # 使用找到的中文字体路径，如果没找到则用默认
    try:
        font = pygame.font.Font(current_font_path, size)
    except:
        # 如果加载失败，回退到默认字体（虽然可能乱码，但保证不崩溃）
        font = pygame.font.SysFont('arial', size)
        
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surf.blit(text_surface, text_rect)

def draw_bar(surf, x, y, pct, color=GREEN):
    if pct < 0: pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    fill = (pct / 100) * BAR_LENGTH
    outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, color, fill_rect)
    pygame.draw.rect(surf, WHITE, outline_rect, 2)

# --- 类定义 ---

class Star(pygame.sprite.Sprite):
    """背景星星"""
    def __init__(self):
        super().__init__()
        self.size = random.randrange(1, 3)
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH)
        self.rect.y = random.randrange(HEIGHT)
        self.speedy = random.randrange(1, 5)

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.rect.y = random.randrange(-20, -5)
            self.rect.x = random.randrange(WIDTH)

class Player(pygame.sprite.Sprite):
    """玩家飞机"""
    def __init__(self, ship_type):
        super().__init__()
        self.ship_type = ship_type
        self.shield = 100
        self.shoot_delay = 250
        self.last_shot = pygame.time.get_ticks()
        self.power = 1 # 火力等级
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()
        self.lives = 3

        # 根据选择的战机类型设定属性
        if ship_type == "SPEED":
            self.image = draw_ship_surface(CYAN, "SPEED")
            self.speed_val = 10
            self.max_shield = 80
            self.shoot_delay = 200
        elif ship_type == "HEAVY":
            self.image = draw_ship_surface(ORANGE, "HEAVY")
            self.speed_val = 5
            self.max_shield = 150
            self.shoot_delay = 300
        else: # BALANCED
            self.image = draw_ship_surface(GREEN, "BALANCED")
            self.speed_val = 8
            self.max_shield = 100
            self.shoot_delay = 250
            
        self.rect = self.image.get_rect()
        self.radius = 20
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.shield = self.max_shield

    def update(self):
        # 隐身（死亡重生时）
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        self.speedx = 0
        self.speedy = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -self.speed_val
        if keystate[pygame.K_RIGHT]:
            self.speedx = self.speed_val
        if keystate[pygame.K_UP]:
            self.speedy = -self.speed_val
        if keystate[pygame.K_DOWN]:
            self.speedy = self.speed_val
        if keystate[pygame.K_SPACE]:
            self.shoot()

        self.rect.x += self.speedx
        self.rect.y += self.speedy

        # 边界限制
        if self.rect.right > WIDTH: self.rect.right = WIDTH
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.bottom > HEIGHT: self.rect.bottom = HEIGHT
        if self.rect.top < 0: self.rect.top = 0

    def shoot(self):
        if self.hidden: return
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            # 根据火力等级发射子弹
            if self.power == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
            if self.power >= 2:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)

    def hide(self):
        # 暂时隐藏玩家
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (WIDTH / 2, HEIGHT + 200)

    def powerup(self):
        self.power += 1
        self.shoot_delay = max(100, self.shoot_delay - 20) # 射速也加快

class Enemy(pygame.sprite.Sprite):
    """敌机"""
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.set_colorkey(BLACK)
        # 绘制敌机外观
        pygame.draw.circle(self.image, RED, (15, 15), 15)
        pygame.draw.rect(self.image, BLACK, (5, 5, 20, 10))
        
        self.rect = self.image.get_rect()
        self.radius = 15
        self.reset_pos()

    def reset_pos(self):
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(2, 8)
        self.speedx = random.randrange(-2, 2)

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT + 10 or self.rect.left < -30 or self.rect.right > WIDTH + 30:
            self.reset_pos()

class Bullet(pygame.sprite.Sprite):
    """子弹"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((8, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -12

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()

class Particle(pygame.sprite.Sprite):
    """爆炸粒子效果"""
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((6, 6))
        self.color = random.choice([ORANGE, RED, YELLOW])
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        # 随机飞散方向
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vel_x = math.cos(angle) * speed
        self.vel_y = math.sin(angle) * speed
        self.life = 30 # 粒子存在帧数

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.life -= 1
        # 颜色渐变或缩小
        if self.life <= 0:
            self.kill()
        else:
            # 简单的闪烁效果
            if self.life % 5 == 0:
                self.image.fill(WHITE)
            else:
                self.image.fill(self.color)

class PowerUp(pygame.sprite.Sprite):
    """掉落道具"""
    def __init__(self, center):
        super().__init__()
        self.type = random.choice(['shield', 'gun'])
        self.image = pygame.Surface((25, 25))
        self.image.set_colorkey(BLACK)
        if self.type == 'shield':
            pygame.draw.circle(self.image, BLUE, (12, 12), 12)
            # 这里也用 draw_text, 但为了避免递归依赖，只绘制简单的图形或字母
            # 注意：如果 draw_text 还是乱码，这里也会乱码，但因为是字母 'S'，Arial也能显示
            draw_text(self.image, "S", 16, 12, 2, WHITE)
        else:
            pygame.draw.rect(self.image, RED, (0, 0, 25, 25))
            draw_text(self.image, "P", 16, 12, 2, WHITE)
            
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 3

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# --- 游戏状态函数 ---

def show_go_screen():
    """游戏结束/开始 屏幕"""
    screen.fill(BLACK)
    draw_text(screen, "雷 霆 战 机", 64, WIDTH / 2, HEIGHT / 4)
    draw_text(screen, "使用方向键移动, 空格射击", 22, WIDTH / 2, HEIGHT / 2)
    draw_text(screen, "按任意键开始", 18, WIDTH / 2, HEIGHT * 3 / 4)
    pygame.display.flip()
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYUP:
                waiting = False

def show_selection_screen():
    """战机选择界面"""
    selection = 0
    ships = ["BALANCED", "SPEED", "HEAVY"]
    labels = ["均衡型 (绿)", "速度型 (青)", "重装型 (橙)"]
    
    while True:
        clock.tick(FPS)
        screen.fill(BLACK)
        draw_text(screen, "选 择 战 机", 48, WIDTH/2, 50)
        
        # 绘制三个选项
        for i, ship_type in enumerate(ships):
            color = WHITE if i == selection else (100, 100, 100)
            y_pos = 200 + i * 100
            draw_text(screen, labels[i], 30, WIDTH/2, y_pos, color)
            # 简单画个示意图
            if ship_type == "SPEED": c = CYAN
            elif ship_type == "HEAVY": c = ORANGE
            else: c = GREEN
            
            # 如果被选中，画箭头
            if i == selection:
                pygame.draw.circle(screen, c, (WIDTH/2 - 120, y_pos + 15), 10)
                pygame.draw.circle(screen, c, (WIDTH/2 + 120, y_pos + 15), 10)

        draw_text(screen, "按 [回车] 或 [空格] 确认", 20, WIDTH/2, HEIGHT - 50)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selection = (selection - 1) % 3
                if event.key == pygame.K_DOWN:
                    selection = (selection + 1) % 3
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return ships[selection]

def spawn_enemy():
    m = Enemy()
    all_sprites.add(m)
    mobs.add(m)

def spawn_explosion(center, amount=20):
    for _ in range(amount):
        p = Particle(center)
        all_sprites.add(p)

# --- 主程序逻辑 ---

game_over = True
running = True
selected_ship_type = "BALANCED"

# 初始显示一次封面
show_go_screen()

while running:
    if game_over:
        selected_ship_type = show_selection_screen() # 选择战机
        
        game_over = False
        # 重置游戏所有组件
        all_sprites = pygame.sprite.Group()
        mobs = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        powerups = pygame.sprite.Group()
        
        # 生成背景星星
        for i in range(50):
            s = Star()
            all_sprites.add(s)
            
        player = Player(selected_ship_type)
        all_sprites.add(player)
        
        for i in range(8):
            spawn_enemy()
            
        score = 0

    clock.tick(FPS)

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 更新
    all_sprites.update()

    # 碰撞检测：子弹击中敌机
    hits = pygame.sprite.groupcollide(mobs, bullets, True, True)
    for hit in hits:
        score += 50 - hit.radius
        spawn_explosion(hit.rect.center) # 播放爆炸粒子
        spawn_enemy() # 生成新敌人
        # 随机掉落道具 (10%概率)
        if random.random() > 0.9:
            pow = PowerUp(hit.rect.center)
            all_sprites.add(pow)
            powerups.add(pow)

    # 碰撞检测：玩家吃到道具
    hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in hits:
        if hit.type == 'shield':
            player.shield += 20
            if player.shield >= player.max_shield:
                player.shield = player.max_shield
        if hit.type == 'gun':
            player.powerup()

    # 碰撞检测：敌机撞到玩家
    hits = pygame.sprite.spritecollide(player, mobs, True, pygame.sprite.collide_circle)
    for hit in hits:
        player.shield -= hit.radius * 2
        spawn_explosion(hit.rect.center)
        spawn_enemy()
        if player.shield <= 0:
            spawn_explosion(player.rect.center, 100) # 大爆炸
            player.hide()
            player.lives -= 1
            player.shield = player.max_shield
            player.power = 1 # 死亡重置火力
            
    # 死亡判定
    if player.lives == 0 and not player.hidden:
        pygame.time.wait(1000)
        game_over = True
        draw_text(screen, "GAME OVER", 50, WIDTH / 2, HEIGHT / 2)
        pygame.display.flip()
        pygame.time.wait(2000)
        show_go_screen()

    # 渲染
    screen.fill(BLACK)
    all_sprites.draw(screen)
    
    # 绘制UI
    draw_text(screen, str(score), 18, WIDTH / 2, 10)
    draw_bar(screen, 5, 5, (player.shield / player.max_shield) * 100, GREEN)
    draw_text(screen, f"Lives: {player.lives}", 18, WIDTH - 50, 10)

    pygame.display.flip()

pygame.quit()