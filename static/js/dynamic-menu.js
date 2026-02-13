
/* Динамическое меню категорий с поддержкой переводов */
class DynamicMenu {
    constructor() {
        this.currentLanguage = document.documentElement.lang ||
            window.LANGUAGE_CODE ||
            this.getCookie('django_language') ||
            'uz';
        
        this.apiUrl = `/api/${this.currentLanguage}/product-categories/`;
        this.categories = [];
        
        this.translations = {
            uz: {
                models: 'Modellar',
                loading: 'Yuklanmoqda...'
            },
            ru: {
                models: 'Модели',
                loading: 'Загрузка...'
            },
            en: {
                models: 'Models',
                loading: 'Loading...'
            }
        };
        
        this.init();
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    t(key) {
        return this.translations[this.currentLanguage]?.[key] || key;
    }
    
    async init() {
        await this.loadCategories();
        this.renderDesktopMenu();
        this.renderMobileMenu();
    }
    
    async loadCategories() {
        try {
            const response = await fetch(this.apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.categories = data.results || data || [];
            
            console.log(`✅ Загружено ${this.categories.length} категорий`);
        } catch (error) {
            console.error('Ошибка загрузки категорий:', error);
            if (window.logJSError) {
                window.logJSError('Categories loading error: ' + error.message, {
                    file: 'dynamic-menu.js',
                    url: this.apiUrl
                });
            }
        }
    }
    
    renderDesktopMenu() {
        const desktopSubmenu = document.querySelector('.desktop-submenu');
        if (!desktopSubmenu) return;
        
        if (this.categories.length === 0) {
            desktopSubmenu.innerHTML = `<li class="desktop-submenu__item"><span>${this.t('loading')}</span></li>`;
            return;
        }
        
        desktopSubmenu.innerHTML = '';
        
        this.categories.forEach(category => {
            const li = document.createElement('li');
            li.className = 'desktop-submenu__item';
            
            const a = document.createElement('a');
            a.href = `/products/?category=${category.slug}`;
            a.className = 'desktop-submenu__link';
            a.textContent = category.name;
            
            li.appendChild(a);
            desktopSubmenu.appendChild(li);
        });
    }
    
    renderMobileMenu() {
        const mobileSubmenu = document.querySelector('.main-menu__accordion .submenu');
        if (!mobileSubmenu) return;
        
        if (this.categories.length === 0) {
            mobileSubmenu.innerHTML = `<li class="submenu__item"><span>${this.t('loading')}</span></li>`;
            return;
        }
        
        mobileSubmenu.innerHTML = '';
        
        this.categories.forEach(category => {
            const li = document.createElement('li');
            li.className = 'submenu__item';
            
            const a = document.createElement('a');
            a.href = `/products/?category=${category.slug}`;
            a.className = 'submenu__link';
            a.textContent = category.name;
            
            li.appendChild(a);
            mobileSubmenu.appendChild(li);
        });
    }
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    new DynamicMenu();
});