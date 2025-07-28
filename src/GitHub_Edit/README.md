<div align="center"><img src="../../other/img/logo.png" width=300 ></div>

## <div align="center">GitHub's Editing Process-GitHub 的編輯流程 </div>
- 在GitHub網頁上編輯非常直觀，適合線上編輯；但新增或刪除檔案、資料夾相對不方便。因此，我們的團隊選擇使用離線編輯。下面我們介紹一下離線編輯的具體方法。

- Editing on the GitHub webpage is very intuitive and suitable for online editing; however, it is relatively inconvenient for adding or deleting files and folders. Therefore, our team has chosen to use offline editing. Below, we introduce the specific methods for offline editing.

- #### Offline Editing with VS Code + Git-使用 VS Code + Git 進行離線編輯:
  以下是使用 VS Code 和 Git 編輯 GitHub 頁面的流程：

  Here’s the process for editing a GitHub page using VS Code and Git:

  #### 1. Install Git and VS Code-安裝 Git 和 VS Code
  - 確保已安裝 Git 和 VS Code。如果沒有，請從官方網站下載並安裝：

  - Make sure Git and VS Code are installed. If not, download and install them from the official websites:
  <ul>
  <li><a href="https://git-scm.com/downloads" target="_blank">Git download page</a></li>
  <li><a href="https://code.visualstudio.com/Download" target="_blank">VS Code download page</a></li>
  </ul>
  

  #### 2. Clone the Repository from GitHub-從 GitHub 複製儲存庫從 GitHub 複製儲存庫
### 中文:
  1. 開啟 VS Code，按下 Ctrl + Shift + P（Mac 請按 Cmd + Shift + P）以開啟指令選單（Command Palette）。
  2. 輸入 Git: Clone 並選擇該選項。
  3. 貼上 GitHub 儲存庫的網址（例如：`https://github.com/username/repo.git`），然後按下 Enter。
  4. 選擇本地資料夾作為儲存位置，VS Code 將自動下載並開啟專案。
### 英文:
  1. Open VS Code and press `Ctrl + Shift + P` (or `Cmd + Shift + P` on Mac) to open the Command Palette.
  2. Type `Git: Clone` and select that option.
  3. Paste the GitHub repository URL (e.g., `https://github.com/username/repo.git`) and press Enter.
  4. Choose a local directory to save the project, and VS Code will automatically download and open it.

  #### 3. Edit Files-編輯文件
  - 現在您可以直接在 VS Code 中瀏覽和編輯專案中的文件。任何變更都會立即顯示在編輯器中。

  - You can now browse and edit files in the project directly in VS Code. Any changes will appear instantly in the editor.

  #### 4. Commit Changes-提交更改
  ### 中文:
  1. 進行變更後，點擊活動欄中的「原始碼控制」圖示（通常是 Git 符號）。 
  2. 在「變更」部分中查看所有未提交的變更。 
  3. 輸入提交訊息，例如“更新index.html”，然後按一下“✓”按鈕進行提交。
  1. After making changes, click on the “Source Control” icon in the activity bar (usually the Git symbol).
  2. Review all uncommitted changes in the “Changes” section.
  3. Enter a commit message, like “Update index.html,” and then click the `✓` button to commit.
### 英文:
  #### 5. Push to GitHub-推送到 GitHub
  ### 中文:
  1. 提交後，點擊「...」選單，選擇「推送」將變更傳送到 GitHub。 
  2.首次推送可能需要登入GitHub並授權連線。
  1. After committing, click the “...” menu and select “Push” to send the changes to GitHub.
  2. For the first push, you may need to log in to GitHub and authorize the connection.
### 英文:
  #### 6. Publish GitHub Pages (if updating a GitHub page)-發布 GitHub 頁面（如果更新 GitHub 頁面）
  ### 中文:
  1. 登入GitHub，進入倉庫頁面。 
  2. 前往「設定」>「頁面」。 
  3. 確保發布分支和目錄（如“main”或“gh-pages”）設定正確。 
  4. 推播變更後，請稍候即可在 GitHub Pages 上看到更新。 

使用 VS Code 和 Git，您可以透過在本地進行編輯並直接推送變更來輕鬆編輯和更新您的 GitHub 頁面。如果一切都配置好了，您可以簡化此過程以便快速編輯和同步。
### 英文:英文:
  1. Log in to GitHub and go to the repository page.
  2. Go to “Settings” > “Pages.”
  3. Ensure the publishing branch and directory (like `main` or `gh-pages`) are set correctly.
  4. Once the changes are pushed, wait a moment to see the updates on GitHub Pages.

  Using VS Code and Git, you can easily edit and update your GitHub page by making edits locally and pushing the changes directly. If everything is configured, you can streamline this process for quick edits and syncing.
<div align="center">
<table>
<tr>
<th>Git Software(Git 軟體)</th>
<th>VS Code Software(VS Code 軟體)</th>
</tr>
<tr>
<td><img src="./img/git.png" alt="git"  width=250/></td>
<td><img src="./img/vscode.png" alt="vscode"  width=450/></td>
</tr>
</table>
</div>

- ### Introduction to Git Software -Git軟體簡介
### 中文:
    - Git 是一個開源分散式版本控制系統，最初由 Linux 的創建者 Linus Torvalds 開發，用於管理大型程式碼儲存庫。主要用於軟體開發，有效追蹤和管理程式碼的歷史變化，支援多個開發人員的協同工作。 
    - Git 的主要特性和功能包括：
    - 版本管理：它追蹤對程式碼所做的每個更改，允許開發人員輕鬆恢復到以前的程式碼狀態並保留程式碼歷史的每個版本。 
    - 分支管理：Git 允許開發人員建立和切換分支，使每個團隊成員能夠在自己的分支上獨立工作，然後將變更合併到主分支中。這對於協作和快速迭代特別有用。 
    - 分散式結構：每個開發人員的本機都有一個完整的儲存庫，這減少了對中央伺服器的依賴並提高了速度和可靠性。 
    - 快速合併和衝突解決：Git 高效合併分支變更並自動偵測衝突，更容易解決平行開發期間出現的問題。 
    - Git 在開發中被廣泛使用，尤其是與 GitHub 和 GitLab 等遠端程式碼託管平台結合使用時，可以讓團隊輕鬆地協作、管理和發布專案。
### 英文:
    Git is an open-source distributed version control system originally developed by Linus Torvalds, the creator of Linux, for managing large code repositories. Primarily used in software development, it effectively tracks and manages the historical changes of code and supports collaborative work among multiple developers.

    Key features and functions of Git include:

    - Version Management: It tracks every change made to the code, allowing developers to easily revert to previous code states and preserve every version of the code’s history.
    - Branch Management: Git allows developers to create and switch branches, enabling each team member to work independently on their own branch and later merge changes into the main branch. This is especially useful for collaboration and fast iteration.
    - Distributed Structure: Each developer’s local machine has a complete repository, which reduces dependence on a central server and increases speed and reliability.
    - Fast Merging and Conflict Resolution: Git efficiently merges branch changes and automatically detects conflicts, making it easier to resolve issues that arise during parallel development.
    
    Git is widely used in development, particularly when combined with remote code hosting platforms like GitHub and GitLab, allowing teams to collaborate, manage, and release projects with ease.
- ### Introduction to Code Editor Software(Visal Studio Code) -程式碼編輯器軟體介紹（Visual Studio Code）
 
  Visual Studio Code（VS Code）是微軟開發的一款免費的、跨平台的程式碼編輯器，廣泛應用於各種開發環境。 VS Code 支援 Windows、macOS 和 Linux，為 Python、JavaScript、C++ 和 Java 等多種程式語言提供內建語法高亮和自動完成功能，非常適合多樣化的開發需求。

  Visual Studio Code (VS Code) is a free, cross-platform code editor developed by Microsoft, widely used in various development environments. VS Code supports Windows, macOS, and Linux, offering built-in syntax highlighting and auto-completion for multiple programming languages, such as Python, JavaScript, C++, and Java, making it ideal for diverse development needs.

__這是一個很棒的選擇！ VS Code 在管理和編輯專案文件方面非常高效，尤其是其整合的 Git 支援和 markdown 預覽功能，使其成為保持 GitHub 儲存庫井然有序和保持最新狀態的理想選擇。__

__That's a great choice! VS Code is highly efficient for managing and editing project documentation, especially with its integrated Git support and markdown preview features, making it ideal for keeping GitHub repos organized and up-to-date.__



# <div align="center">![HOME](../../other/img/home.png)[Return Home](../../)</div>  


