import math
import os
import random
import sys
import time
import pygame as pg

# ウィンドウのサイズ設定
WIDTH = 1100  
HEIGHT = 650  

# カレントディレクトリの設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 境界のチェック関数
def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate

# 目標位置に向かう方向を計算する関数
def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class EMP(pg.sprite.Sprite):
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        super().__init__()
        self.emys = emys
        self.bombs = bombs
        self.screen = screen
        self.duration =3

        self.image = pg.Surface((WIDTH, HEIGHT))
        self.image.set_alpha(128)  
        self.image.fill((255, 255, 0))

        self.rect = self.image.get_rect()  
        self.rect.topleft = (0, 0)

        for emy in self.emys:
            emy.interval = float('inf')
            emy.image.set_alpha(128)

        for bomb in self.bombs:
            bomb.speed /= 2
             
    def update(self):
        
        self.duration -= 0.05
        if self.duration <= 0:
           self.kill()

class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }


    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
            "normal": img0,  # 通常状態
            "hyper": pg.transform.rotozoom(pg.image.load("fig/11.png"), 0, 2.0),  # 無敵状態
            "sad": pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 2.0),  # 悲しみ状態
        }
        self.dire = (+1, 0)
        self.image = self.imgs["normal"]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):

        sum_mv = [0, 0]
        current_speed = self.speed  # デフォルトスピードは10
        if key_lst[pg.K_LSHIFT]:  # 左Shiftキーが押されたとき
            current_speed = 20  # 高速化する
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)

        # キャラクターの画像を状態に応じて設定
        if self.state == "hyper":
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"
            else:
                # 無敵状態の時も方向に応じた画像に変更
                self.image = self.imgs[self.dire]  # 方向に応じた画像
                self.image = pg.transform.laplacian(self.image)  # 無敵エフェクトを適用
        elif self.state == "sad":
            # ゲームオーバー時の悲しみ状態の画像を設定
            self.image = self.imgs["sad"]
        else:
            # 通常状態の画像を方向に応じて設定
            self.image = self.imgs[self.dire]

        screen.blit(self.image, self.rect)

# 爆弾のクラス
class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径
        self.image = pg.Surface((2 * rad, 2 * rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery + emy.rect.height // 2
        self.speed = 6

    def update(self):
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

# ビームのクラス
class Beam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

# 爆発のクラス
class Explosion(pg.sprite.Sprite):
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life // 10 % 2]
        if self.life < 0:
            self.kill()

# 敵キャラクターのクラス
class Enemy(pg.sprite.Sprite):
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT // 2)
        self.state = "down"
        self.interval = random.randint(50, 300)

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)

# スコアのクラス
class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT - 50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Gravity(pg.sprite.Sprite):
    """
    重力場に関するクラス
    """
    def __init__(self, life: int):
        """
        重力場Surfaceを生成する
        引数1 life：重力場の発動時間
        """
        super().__init__()
        self.image = pg.Surface((1100, 650))  # 画面全体を覆うサイズ
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, 1100, 650))  # 黒い矩形を描画
        self.image.set_alpha(128)  # 半透明度を設定
        self.rect = self.image.get_rect()
        self.life = life

    def update(self, bombs: pg.sprite.Group, enemies: pg.sprite.Group, exps: pg.sprite.Group):
        """
        重力場の発動中は爆弾や敵機を削除し、エフェクトを発生させる
        """
        self.life -= 1
        if self.life < 0:
            self.kill()
        # 重力場内の爆弾をすべて削除
        for bomb in bombs:
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            bomb.kill()
        # 重力場内の敵機をすべて削除
        for enemy in enemies:
            exps.add(Explosion(enemy, 100))  # 爆発エフェクト
            enemy.kill()

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    emps = pg.sprite.Group()
    gravitys = pg.sprite.Group()  # 重力場のグループ

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_RETURN and score.value >= 200:  # 重力場発動条件
                    gravitys.add(Gravity(400))  # 重力場発動
                    score.value -= 200  # スコアを200消費
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if score.value >= 20:
                       emps.add(EMP(emys, bombs, screen))
                       score.value -= 20
                       
        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            if bird.state != "hyper":
                bird.image = bird.imgs["sad"]
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            else:
                score.value += 1  # 無敵状態での当たり
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        emps.update()  
        emps.draw(screen) 
        gravitys.update(bombs, emys, exps)  # 修正: gravitys を更新
        gravitys.draw(screen)  # 修正: gravitys を描画
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)



if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
