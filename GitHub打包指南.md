# GitHub Actions 自动打包指南

通过 GitHub 的免费云服务器自动打包 Windows .exe，全程不需要 Windows 电脑。

---

## 整体流程

```
你的 Mac                    GitHub 云服务器（Windows）
    │                               │
    ├─ 推送代码 ──────────────────→ │
    │                               ├─ 自动安装 Python 3.10
    │                               ├─ 自动安装依赖
    │                               ├─ 自动打包为 .exe
    │                               │
    ← 下载 ExamClient.exe ──────────┤
    │
    ├─ U盘拷贝给同事
```

整个打包过程约 3~5 分钟，完全自动，你只需要上传代码和下载结果。

---

## 第一步：在 GitHub 创建仓库

1. 打开浏览器，访问 `https://github.com`，登录你的账号

2. 点击右上角的 **+** 号，选择 **New repository**

```
┌──────────────────────────────────────────────────┐
│  Create a new repository                         │
│                                                  │
│  Repository name: exam_client                    │
│                                                  │
│  Description: 离线题库练习系统（可不填）           │
│                                                  │
│  ● Private   ← 选私有，代码不公开                 │
│  ○ Public                                        │
│                                                  │
│  不要勾选任何初始化选项（README、.gitignore 等）  │
│                                                  │
│  [Create repository]                             │
└──────────────────────────────────────────────────┘
```

3. 点击 **Create repository**

4. 创建成功后，页面会显示一个仓库地址，类似：
   ```
   https://github.com/你的用户名/exam_client.git
   ```
   **复制这个地址备用**

---

## 第二步：在 Mac 上配置 git 并推送代码

打开终端（Mac 上按 `Command + 空格`，输入"终端"，回车），
按顺序输入以下命令（每行输完按回车）：

### 2-1 配置 git 身份（只需做一次）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

将引号内替换为你自己的信息，邮箱用注册 GitHub 时的邮箱。

### 2-2 进入项目目录

```bash
cd /Users/domiiadedianjita/exam_client
```

### 2-3 初始化 git 仓库并推送

```bash
# 初始化本地仓库
git init

# 将所有文件加入暂存区
git add .

# 创建第一次提交
git commit -m "初始提交"

# 将默认分支命名为 main
git branch -M main

# 关联远程仓库（将下面的地址替换为你刚才复制的地址）
git remote add origin https://github.com/你的用户名/exam_client.git

# 推送代码
git push -u origin main
```

### 2-4 输入 GitHub 密码

推送时终端会提示输入用户名和密码：

```
Username for 'https://github.com': 你的GitHub用户名
Password for 'https://你的用户名@github.com':
```

**注意：** GitHub 已不支持直接用账号密码，需要用 **Personal Access Token** 代替密码。

**获取 Token 的步骤：**

1. 在浏览器中访问：`https://github.com/settings/tokens/new`
2. 填写 Note（备注）：`exam_client`
3. Expiration（有效期）：选 **90 days** 或 **No expiration**
4. 勾选权限：**repo**（勾选这一项会自动勾选所有子项）
5. 点击底部 **Generate token**
6. 页面显示一串以 `ghp_` 开头的字符串，**立即复制**（只显示一次）

回到终端，在 Password 提示处粘贴这串 Token（粘贴时屏幕不显示任何字符，属正常现象），回车。

---

## 第三步：查看打包进度

推送成功后，GitHub 会自动开始打包。

1. 在浏览器中打开你的仓库页面：
   `https://github.com/你的用户名/exam_client`

2. 点击顶部的 **Actions** 标签

```
┌─────────────────────────────────────────────────────────┐
│  Code  Issues  Pull requests  Actions  ...              │
│                              ↑ 点这里                   │
├─────────────────────────────────────────────────────────┤
│  All workflows                                          │
│                                                         │
│  ● 打包 Windows .exe    初始提交    运行中...  2分钟前  │
│                         ↑ 点击查看详情                  │
└─────────────────────────────────────────────────────────┘
```

3. 点击那条记录，可以看到实时日志

4. 左侧圆圈的颜色含义：
   - 🟡 黄色旋转：正在运行
   - ✅ 绿色对勾：成功
   - ❌ 红色叉号：失败（查看日志找原因）

---

## 第四步：下载 .exe 文件

打包成功后（绿色对勾）：

1. 点击那条成功的运行记录
2. 滚动到页面底部，找到 **Artifacts** 区域

```
┌─────────────────────────────────────────────────────────┐
│  Artifacts                                              │
│                                                         │
│  ExamClient-Windows                    7.2 MB  [下载↓] │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

3. 点击 **ExamClient-Windows** 下载
4. 下载得到一个 zip 压缩包，解压后得到 `ExamClient.exe`

---

## 第五步：分发给同事

将 `ExamClient.exe` 通过 U 盘复制到每台同事的电脑，双击即可运行，无需安装任何软件。

---

## 以后更新程序

每次修改代码后，在终端执行以下命令重新触发打包：

```bash
cd /Users/domiiadedianjita/exam_client

# 将修改的文件加入暂存区
git add .

# 提交（引号内填写本次修改的说明）
git commit -m "修复某某问题"

# 推送，自动触发重新打包
git push
```

也可以在 GitHub 网页上手动触发：
Actions → 左侧选「打包 Windows .exe」→ 右侧点「Run workflow」→「Run workflow」

---

## 常见问题

**Q：push 时提示 "src refspec main does not match any"**

A：说明还没有提交。先执行：
```bash
git add .
git commit -m "初始提交"
git push -u origin main
```

---

**Q：push 时提示 "remote: Repository not found"**

A：远程地址填错了。检查并重新设置：
```bash
git remote set-url origin https://github.com/你的正确用户名/exam_client.git
git push -u origin main
```

---

**Q：Actions 运行失败，日志显示 "No module named..." 或打包报错**

A：点击失败的步骤展开日志，将错误信息截图，可以在本对话中发给我排查。

---

**Q：Artifacts 下载后解压得到的 .exe 能在 Win7 上运行吗？**

A：可以。GitHub Actions 使用 Windows Server 2019 打包，生成的 .exe 兼容 Win7 SP1 x64 及以上系统。
