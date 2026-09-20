import styles from "./Sidebar.module.css"
import { LogoutIcon } from "../Icons/Icons"
import { Link } from "react-router-dom"
import BackendTerminal from "../BackendTerminal/BackendTerminal"

export default function Sidebar({
  isOpen,
  width,
  isResizing,
  onResizeStart,
  chatHistory,
  activeChatId,
  onSelectChat,
  currentUser,
  terminalLogs = [],
  isTyping = false,
  onClearTerminal,
}) {
  return (
    <aside
      className={`${styles.sidebar}${isOpen ? "" : ` ${styles.collapsed}`}`}
      style={{
        width: isOpen ? width : 0,
        transition: isResizing ? "none" : undefined,
      }}
    >
      <div className={styles.sidebarBrand}>
        <div className={styles.sidebarBrandMark}>CI</div>
        <div className={styles.sidebarBrandText}>
          Charaka IP
        </div>
      </div>

      <div className={styles.historyLabel}>Recent</div>
      <nav className={styles.historyList}>
        {chatHistory.map((chat) => (
          <button
            type="button"
            key={chat.id}
            className={`${styles.historyItem}${chat.id === activeChatId ? ` ${styles.active}` : ""}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <span className={styles.historyItemTitle}>{chat.title}</span>
            <span className={styles.historyItemDate}>{chat.date}</span>
          </button>
        ))}
      </nav>

      <BackendTerminal
        logs={terminalLogs}
        isRunning={isTyping}
        onClear={onClearTerminal}
      />

      <div className={styles.sidebarFooter}>
        <div className={styles.profileRow}>
          <div className={`${styles.profileAvatar} ${styles.nmInset}`}>
            {currentUser.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div>
            <div className={styles.profileName}>{currentUser.name}</div>
            <div className={styles.profileRole}>{currentUser.role}</div>
          </div>
        </div>
        <Link to="/" className={styles.logoutLink}>
          <button type="button" className={styles.logoutBtn}>
            <LogoutIcon />
            Log out
          </button>
        </Link>
      </div>

      {isOpen && (
        <div
          className={styles.resizer}
          onMouseDown={onResizeStart}
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize chat history panel"
        />
      )}
    </aside>
  )
}
