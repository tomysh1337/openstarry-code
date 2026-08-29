// 复制代码功能
function copyCode(button) {
    const codeBlock = button.closest('.code-block');
    const code = codeBlock.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.style.background = 'rgba(34, 197, 94, 0.3)';
        button.style.color = '#86efac';
        button.style.borderColor = 'rgba(34, 197, 94, 0.5)';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = 'rgba(139, 92, 246, 0.2)';
            button.style.color = '#a78bfa';
            button.style.borderColor = 'rgba(139, 92, 246, 0.3)';
        }, 2000);
    }).catch(err => {
        console.error('复制失败:', err);
        button.textContent = '复制失败';
        setTimeout(() => {
            button.textContent = '复制';
        }, 2000);
    });
}

// 标签页切换
function switchTab(event, tabId) {
    // 移除所有 active 类
    const tabButtons = event.target.parentElement.querySelectorAll('.tab-btn');
    const tabContents = event.target.closest('.card').querySelectorAll('.tab-content');
    
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));
    
    // 激活当前标签
    event.target.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// 导航链接高亮
function updateActiveNav() {
    const sections = document.querySelectorAll('.doc-section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    let currentSection = '';
    
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (window.pageYOffset >= sectionTop - 100) {
            currentSection = section.getAttribute('id');
        }
    });
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === '#' + currentSection) {
            link.classList.add('active');
        }
    });
}

// 平滑滚动
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// 监听滚动事件
window.addEventListener('scroll', updateActiveNav);

// 页面加载完成
document.addEventListener('DOMContentLoaded', () => {
    updateActiveNav();
    
    // 添加加载动画
    const cards = document.querySelectorAll('.card, .feature-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    entry.target.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach(card => observer.observe(card));
});

// 移动端侧边栏切换
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('open');
}

// 键盘快捷键
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K 打开搜索（预留）
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        console.log('搜索功能（待实现）');
    }
});
