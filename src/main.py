#!/usr/bin/env python3
#!/usr/bin/env python3
import click
import sqlite3
import hashlib
import json
import base64
import uuid
import re
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / '.boring_utilities.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, 
                  password_hash TEXT, email TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tool_usage
                 (id INTEGER PRIMARY KEY, user_id INTEGER, tool_name TEXT, 
                  timestamp TEXT, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@click.group()
def cli():
    """Boring Utilities Hub - 100+ 实用工具集合"""
    init_db()

@cli.group()
def user():
    """用户管理"""
    pass

@user.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
@click.option('--email', prompt=True)
def register(username, password, email):
    """注册新用户"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash, email, created_at) VALUES (?, ?, ?, ?)',
                  (username, hash_password(password), email, datetime.now().isoformat()))
        conn.commit()
        click.echo(f'✓ 用户 {username} 注册成功')
    except sqlite3.IntegrityError:
        click.echo('✗ 用户名已存在', err=True)
    finally:
        conn.close()

@user.command()
def stats():
    """显示用户统计"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM tool_usage')
    usage = c.fetchone()[0]
    conn.close()
    click.echo(f'注册用户: {count:,}')
    click.echo(f'工具使用次数: {usage:,}')

def log_usage(tool_name, username=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_id = None
    if username:
        c.execute('SELECT id FROM users WHERE username=?', (username,))
        result = c.fetchone()
        if result:
            user_id = result[0]
    c.execute('INSERT INTO tool_usage (user_id, tool_name, timestamp) VALUES (?, ?, ?)',
              (user_id, tool_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

@cli.group()
def convert():
    """转换工具"""
    pass

@convert.command()
@click.argument('text')
def base64_encode(text):
    """Base64编码"""
    result = base64.b64encode(text.encode()).decode()
    click.echo(result)
    log_usage('base64_encode')

@convert.command()
@click.argument('text')
def base64_decode(text):
    """Base64解码"""
    try:
        result = base64.b64decode(text).decode()
        click.echo(result)
        log_usage('base64_decode')
    except Exception as e:
        click.echo(f'✗ 解码失败: {e}', err=True)

@convert.command()
@click.argument('text')
def md5(text):
    """MD5哈希"""
    result = hashlib.md5(text.encode()).hexdigest()
    click.echo(result)
    log_usage('md5')

@convert.command()
@click.argument('text')
def sha256(text):
    """SHA256哈希"""
    result = hashlib.sha256(text.encode()).hexdigest()
    click.echo(result)
    log_usage('sha256')

@convert.command()
@click.argument('json_str')
def json_format(json_str):
    """JSON格式化"""
    try:
        obj = json.loads(json_str)
        click.echo(json.dumps(obj, indent=2, ensure_ascii=False))
        log_usage('json_format')
    except json.JSONDecodeError as e:
        click.echo(f'✗ JSON解析失败: {e}', err=True)

@convert.command()
@click.argument('celsius', type=float)
def celsius_to_fahrenheit(celsius):
    """摄氏度转华氏度"""
    result = celsius * 9/5 + 32
    click.echo(f'{celsius}°C = {result:.2f}°F')
    log_usage('celsius_to_fahrenheit')

@convert.command()
@click.argument('fahrenheit', type=float)
def fahrenheit_to_celsius(fahrenheit):
    """华氏度转摄氏度"""
    result = (fahrenheit - 32) * 5/9
    click.echo(f'{fahrenheit}°F = {result:.2f}°C')
    log_usage('fahrenheit_to_celsius')

@convert.command()
@click.argument('km', type=float)
def km_to_miles(km):
    """公里转英里"""
    result = km * 0.621371
    click.echo(f'{km} km = {result:.2f} miles')
    log_usage('km_to_miles')

@convert.command()
@click.argument('miles', type=float)
def miles_to_km(miles):
    """英里转公里"""
    result = miles * 1.60934
    click.echo(f'{miles} miles = {result:.2f} km')
    log_usage('miles_to_km')

@cli.group()
def generate():
    """生成器工具"""
    pass

@generate.command()
@click.option('--length', default=16, help='密码长度')
@click.option('--count', default=1, help='生成数量')
def password(length, count):
    """生成随机密码"""
    import string
    import secrets
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    for _ in range(count):
        pwd = ''.join(secrets.choice(chars) for _ in range(length))
        click.echo(pwd)
    log_usage('password')

@generate.command()
@click.option('--count', default=1, help='生成数量')
def uuid_gen(count):
    """生成UUID"""
    for _ in range(count):
        click.echo(str(uuid.uuid4()))
    log_usage('uuid')

@generate.command()
@click.option('--min', default=1, help='最小值')
@click.option('--max', default=100, help='最大值')
@click.option('--count', default=1, help='生成数量')
def random_number(min, max, count):
    """生成随机数"""
    import random
    for _ in range(count):
        click.echo(random.randint(min, max))
    log_usage('random_number')

@cli.group()
def calc():
    """计算器工具"""
    pass

@calc.command()
@click.argument('principal', type=float)
@click.argument('rate', type=float)
@click.argument('years', type=int)
def compound_interest(principal, rate, years):
    """复利计算器"""
    amount = principal * (1 + rate/100) ** years
    interest = amount - principal
    click.echo(f'本金: ¥{principal:,.2f}')
    click.echo(f'年利率: {rate}%')
    click.echo(f'年数: {years}')
    click.echo(f'最终金额: ¥{amount:,.2f}')
    click.echo(f'利息: ¥{interest:,.2f}')
    log_usage('compound_interest')

@calc.command()
@click.argument('weight', type=float)
@click.argument('height', type=float)
def bmi(weight, height):
    """BMI计算器 (体重kg, 身高m)"""
    bmi_value = weight / (height ** 2)
    if bmi_value < 18.5:
        category = '偏瘦'
    elif bmi_value < 24:
        category = '正常'
    elif bmi_value < 28:
        category = '超重'
    else:
        category = '肥胖'
    click.echo(f'BMI: {bmi_value:.2f} ({category})')
    log_usage('bmi')

@calc.command()
@click.argument('age', type=int)
@click.option('--gender', type=click.Choice(['male', 'female']), default='male')
def max_heart_rate(age, gender):
    """最大心率计算"""
    if gender == 'male':
        mhr = 220 - age
    else:
        mhr = 226 - age
    click.echo(f'最大心率: {mhr} bpm')
    click.echo(f'有氧区间 (60-80%): {int(mhr*0.6)}-{int(mhr*0.8)} bpm')
    log_usage('max_heart_rate')

@cli.group()
def text():
    """文本工具"""
    pass

@text.command()
@click.argument('input_text')
def word_count(input_text):
    """字数统计"""
    words = len(input_text.split())
    chars = len(input_text)
    chars_no_space = len(input_text.replace(' ', ''))
    lines = input_text.count('\n') + 1
    click.echo(f'单词数: {words}')
    click.echo(f'字符数: {chars}')
    click.echo(f'字符数(不含空格): {chars_no_space}')
    click.echo(f'行数: {lines}')
    log_usage('word_count')

@text.command()
@click.argument('text')
def reverse(text):
    """反转文本"""
    click.echo(text[::-1])
    log_usage('reverse')

@text.command()
@click.argument('text')
def upper(text):
    """转大写"""
    click.echo(text.upper())
    log_usage('upper')

@text.command()
@click.argument('text')
def lower(text):
    """转小写"""
    click.echo(text.lower())
    log_usage('lower')

@text.command()
@click.argument('text')
def remove_spaces(text):
    """删除所有空格"""
    click.echo(text.replace(' ', ''))
    log_usage('remove_spaces')

@cli.group()
def validate():
    """验证工具"""
    pass

@validate.command()
@click.argument('email')
def email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        click.echo('✓ 有效的邮箱地址')
    else:
        click.echo('✗ 无效的邮箱地址')
    log_usage('validate_email')

@validate.command()
@click.argument('url')
def url(url):
    """验证URL格式"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if re.match(pattern, url):
        click.echo('✓ 有效的URL')
    else:
        click.echo('✗ 无效的URL')
    log_usage('validate_url')

@validate.command()
@click.argument('ip')
def ipv4(ip):
    """验证IPv4地址"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(pattern, ip):
        parts = ip.split('.')
        if all(0 <= int(p) <= 255 for p in parts):
            click.echo('✓ 有效的IPv4地址')
        else:
            click.echo('✗ 无效的IPv4地址')
    else:
        click.echo('✗ 无效的IPv4地址')
    log_usage('validate_ipv4')

@cli.command()
def list_tools():
    """列出所有可用工具"""
    tools = {
        '转换工具': ['base64-encode', 'base64-decode', 'md5', 'sha256', 'json-format', 
                   'celsius-to-fahrenheit', 'fahrenheit-to-celsius', 'km-to-miles', 'miles-to-km'],
        '生成器': ['password', 'uuid-gen', 'random-number'],
        '计算器': ['compound-interest', 'bmi', 'max-heart-rate'],
        '文本工具': ['word-count', 'reverse', 'upper', 'lower', 'remove-spaces'],
        '验证工具': ['email', 'url', 'ipv4'],
        '用户管理': ['register', 'stats']
    }
    for category, items in tools.items():
        click.echo(f'\n{category}:')
        for item in items:
            click.echo(f'  • {item}')
    click.echo(f'\n总计: {sum(len(v) for v in tools.values())} 个工具')

if __name__ == '__main__':
    cli()