/**
 * FAW Products - Динамическая загрузка карточек с поддержкой переводов
 * Обновлено: загрузка категорий из API
 */

class ProductsManager {
  constructor() {
    // Определяем текущий язык
    this.currentLanguage = document.documentElement.lang ||
      window.LANGUAGE_CODE ||
      this.getCookie('django_language') ||
      'uz';

    // Определяем API URL в зависимости от языка
    this.apiUrl = `/api/${this.currentLanguage}/products/`;
    this.categoriesApiUrl = `/api/${this.currentLanguage}/product-categories/`;
    
    this.currentCategory = null;
    this.currentPage = 1;
    this.cardsPerPage = 8;
    this.allProducts = [];
    this.filteredProducts = [];
    this.categories = []; // ✅ Категории из API
    this.currentCategoryData = null; // ✅ Данные текущей категории

    // Переводы для UI элементов
    this.translations = {
      uz: {
        buttonText: 'Batafsil o\'qish',
        loading: 'Yuklanmoqda...',
        noResults: 'Mahsulotlar topilmadi',
        error: 'Xatolik yuz berdi',
        tryAgain: 'Keyinroq urinib ko\'ring yoki sahifani yangilang',
        prev: 'Ortga',
        next: 'Oldinga'
      },
      ru: {
        buttonText: 'Подробнее',
        loading: 'Загрузка...',
        noResults: 'Товары не найдены',
        error: 'Произошла ошибка',
        tryAgain: 'Попробуйте позже или обновите страницу',
        prev: 'Назад',
        next: 'Вперёд'
      },
      en: {
        buttonText: 'Read more',
        loading: 'Loading...',
        noResults: 'No products found',
        error: 'An error occurred',
        tryAgain: 'Please try again later or refresh the page',
        prev: 'Previous',
        next: 'Next'
      }
    };

    this.init();
  }

  // Получаем перевод
  t(key) {
    return this.translations[this.currentLanguage]?.[key] || key;
  }

  // Получаем cookie
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  async init() {
    // Получаем категорию из URL
    const urlParams = new URLSearchParams(window.location.search);
    this.currentCategory = urlParams.get('category');

    // ✅ Загружаем категории из API
    await this.loadCategories();

    // Обновляем все элементы страницы
    this.updatePageContent();

    // Загружаем продукты
    await this.loadProducts();

    // Инициализируем поиск
    this.initSearch();
  }

async loadCategories() {
    try {
      const response = await fetch(this.categoriesApiUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.categories = data.results || data || [];
      
      console.log(`✅ Загружено ${this.categories.length} категорий`);
      
      // ✅ Выводим структуру категории для отладки
      if (this.categories.length > 0) {
        console.log('📦 Структура категории:', this.categories[0]);
      }

      // Находим данные текущей категории
      if (this.currentCategory) {
        this.currentCategoryData = this.categories.find(
          cat => cat.slug === this.currentCategory
        );
        
        if (this.currentCategoryData) {
          console.log('✅ Данные текущей категории:', this.currentCategoryData);
        } else {
          console.warn('⚠️ Категория не найдена:', this.currentCategory);
        }
      }
    } catch (error) {
      console.error('❌ Categories loading error:', error);
      if (window.logJSError) {
        window.logJSError('Categories loading error: ' + error.message, {
          file: 'products.js',
          url: this.categoriesApiUrl
        });
      }
    }
  }

   updatePageContent() {
    if (!this.currentCategory || !this.currentCategoryData) {
      console.log('⚠️ No category specified or category data not loaded');
      return;
    }

    console.log('🔄 Обновляем контент страницы для:', this.currentCategoryData.name);

    // 1. ✅ Обновляем заголовок
    const titleElement = document.querySelector('.models_title');
    if (titleElement) {
      titleElement.textContent = this.currentCategoryData.name;
      console.log('✅ Заголовок обновлён:', this.currentCategoryData.name);
    }

    // 2. ✅ Обновляем описание
    const descriptionElement = document.querySelector('.hero-05-title__item:not(.title-item-image)');
    if (descriptionElement && this.currentCategoryData.description) {
      descriptionElement.textContent = this.currentCategoryData.description;
      console.log('✅ Описание обновлено:', this.currentCategoryData.description);
    } else {
      console.log('⚠️ Описание не найдено или элемент отсутствует');
    }

    // 3. ✅ Обновляем HERO ИЗОБРАЖЕНИЕ
    const heroImage = document.querySelector('.mxd-hero-06__img img');
    if (heroImage && this.currentCategoryData.hero_image_url) {
      heroImage.src = this.currentCategoryData.hero_image_url;
      heroImage.alt = this.currentCategoryData.name;
      console.log('✅ Hero изображение обновлено:', this.currentCategoryData.hero_image_url);
    } else if (heroImage && !this.currentCategoryData.hero_image_url) {
      console.log('⚠️ Hero изображение не загружено в категорию');
    } else {
      console.log('⚠️ Элемент hero изображения не найден');
    }

    // 4. ✅ Обновляем хлебные крошки
    const breadcrumbActive = document.querySelector('.breadcrumb-ol .active a');
    if (breadcrumbActive) {
      breadcrumbActive.textContent = this.currentCategoryData.name;
      console.log('✅ Хлебные крошки обновлены');
    }

    // 5. ✅ Обновляем title страницы
    document.title = `${this.currentCategoryData.name} - Autoliga`;
    console.log('✅ Title страницы обновлён');
  }

  async loadProducts() {
    try {
      this.showLoader();

      // Загружаем ВСЕ страницы
      let allProducts = [];
      let nextUrl = this.apiUrl;

      while (nextUrl) {
        const response = await fetch(nextUrl);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Добавляем продукты из текущей страницы
        const products = data.results || data.products || data || [];
        allProducts = allProducts.concat(products);

        // Приводим URL к текущему протоколу
        if (data.next) {
          try {
            const url = new URL(data.next);
            nextUrl = url.pathname + url.search;
          } catch (e) {
            nextUrl = data.next;
          }
        } else {
          nextUrl = null;
        }
      }

      this.allProducts = allProducts;
      console.log(`✅ Загружено ${this.allProducts.length} продуктов`);

      // ФИЛЬТРУЕМ продукты по категории
      if (this.currentCategory) {
        this.filteredProducts = this.allProducts.filter(product => {
          // ✅ Проверяем category.slug (не category === slug)
          return product.category && product.category.slug === this.currentCategory;
        });

        console.log(`✅ Найдено ${this.filteredProducts.length} продуктов в категории "${this.currentCategory}"`);
      } else {
        this.filteredProducts = [...this.allProducts];
      }

      if (this.filteredProducts.length === 0) {
        this.showNoResults();
        return;
      }

      this.renderCards();
      this.createPagination();
      this.hideLoader();

    } catch (error) {
      console.error('Products loading error:', error);
      if (window.logJSError) {
        window.logJSError('Products loading error: ' + error.message, {
          file: 'products.js',
          category: this.currentCategory,
          url: this.apiUrl
        });
      }
      this.showError(error.message);
    }
  }

  renderCards() {
    const container = document.querySelector('.faw-truck-card-container');
    if (!container) {
      window.logJSError('Container .faw-truck-card-container not found', { file: 'products.js' });
      return;
    }

    container.innerHTML = '';

    const start = (this.currentPage - 1) * this.cardsPerPage;
    const end = start + this.cardsPerPage;
    const cardsToShow = this.filteredProducts.slice(start, end);

    if (cardsToShow.length === 0) {
      this.showNoResults();
      return;
    }

    cardsToShow.forEach(product => {
      const cardHTML = this.createCardHTML(product);
      const wrapper = document.createElement('div');
      wrapper.className = 'product-card-wrapper';
      wrapper.innerHTML = cardHTML;
      container.appendChild(wrapper);
    });
  }

  // createCardHTML(product) {
  //   // Проверяем наличие спецификаций
  //   let specsHTML = '';
  //   if (product.card_specs && Array.isArray(product.card_specs)) {
  //     specsHTML = product.card_specs
  //       .sort((a, b) => (a.order || 0) - (b.order || 0))
  //       .map(spec => {
  //         const iconUrl = spec.icon?.icon_url || spec.icon_url || '';
  //         const iconName = spec.icon?.name || spec.name || '';
  //         const specValue = spec.value || '';
  //         return `
  //           <div class="spec-item">
  //             ${iconUrl ? `<img class="spec-icon" src="${iconUrl}" alt="${iconName}">` : ''}
  //             <span class="spec-value">${specValue}</span>
  //           </div>
  //         `;
  //       }).join('');
  //   }

  //   // Формируем URL изображения
  //   const imageUrl = product.image_url || product.image || product.main_image || '';
  //   const productSlug = product.slug || '';
  //   const productTitle = product.title || product.name || 'Продукт';
  //   const buttonText = this.t('buttonText');

  //   return `
  //     <div class="faw-truck-card">
  //       <div class="truck-image-container">
  //         ${imageUrl ? `<img src="${imageUrl}"  class="truck-image">` : ''}
  //       </div>
  //       <div class="truck-info">
  //         ${specsHTML ? `<div class="truck-specs">${specsHTML}</div>` : ''}
  //         <div class="truck-cta">
  //           <a href="/products/${productSlug}/" class="btn-details">${buttonText}</a>
  //         </div>
  //       </div>
  //     </div>
  //   `;
  // }

  createCardHTML(product) {
      // 1. Texnik xususiyatlar (Ikonkalar)
      let specsHTML = '';
      if (product.card_specs && Array.isArray(product.card_specs)) {
        specsHTML = product.card_specs
          .sort((a, b) => (a.order || 0) - (b.order || 0))
          .map(spec => {
            const iconUrl = spec.icon?.icon_url || spec.icon_url || '';
            const specValue = spec.value || '';
            return `
              <div class="spec-item">
                ${iconUrl ? `<img class="spec-icon" src="${iconUrl}" alt="">` : ''}
                <span class="spec-value">${specValue}</span>
              </div>
            `;
          }).join('');
      }

      // 2. Ma'lumotlarni tayyorlash
      const imageUrl = product.image_url || product.image || product.main_image || '';
      const productSlug = product.slug || '';
      const buttonText = this.t('buttonText');
      const brandName = product.category ? product.category.name : '';
      const productTitle = product.title || product.name || '';
      
      // Narx: avval slider_price, bo'lmasa oddiy price maydonidan olamiz
      const displayPrice = product.slider_price || product.price || '';

      return `
        <div class="faw-truck-card">
          <div class="truck-image-container">
            ${brandName ? `<div class="brand-badge">${brandName}</div>` : ''}
            ${imageUrl ? `<img src="${imageUrl}" class="truck-image">` : ''}
          </div>
          
          <div class="truck-info">
            <h3 class="truck-title">${productTitle}</h3>
            
        
            ${displayPrice ? `
            <div class="truck-price">
              <span>${displayPrice}</span>
            </div>
            ` : ''}
            ${specsHTML ? `<div class="truck-specs">${specsHTML}</div>` : ''}
            
            <div class="truck-cta">
              <a href="/products/${productSlug}/" class="btn-details">${buttonText}</a>
            </div>
          </div>
        </div>
      `;
    }

  createPagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const totalPages = Math.ceil(this.filteredProducts.length / this.cardsPerPage);

    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    pagination.innerHTML = '';

    // Кнопка "Назад"
    const prevButton = this.createButton('prev', this.t('prev'), this.currentPage > 1);
    prevButton.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.currentPage > 1) {
        this.currentPage--;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      }
    });
    pagination.appendChild(prevButton);

    // Номера страниц
    for (let i = 1; i <= totalPages; i++) {
      const pageButton = document.createElement('a');
      pageButton.href = 'javascript:void(0);';
      pageButton.className = `mxd-blog-pagination__item blog-pagination-number btn btn-anim ${i === this.currentPage ? 'active' : ''}`;
      pageButton.innerHTML = `<span class="btn-caption">${i}</span>`;
      pageButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.currentPage = i;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      });
      pagination.appendChild(pageButton);
    }

    // Кнопка "Вперед"
    const nextButton = this.createButton('next', this.t('next'), this.currentPage < totalPages);
    nextButton.addEventListener('click', (e) => {
      e.preventDefault();
      if (this.currentPage < totalPages) {
        this.currentPage++;
        this.renderCards();
        this.updatePagination();
        this.scrollToTop();
      }
    });
    pagination.appendChild(nextButton);
  }

  createButton(type, text, enabled) {
    const button = document.createElement('a');
    button.href = 'javascript:void(0);';
    button.className = `mxd-blog-pagination__item blog-pagination-control ${type} btn btn-anim btn-line-small btn-bright anim-no-delay slide-${type === 'prev' ? 'left' : 'right'}`;

    if (!enabled) button.classList.add('disabled');

    if (type === 'prev') {
      button.innerHTML = `<i class="ph ph-arrow-left"></i><span class="btn-caption">${text}</span>`;
    } else {
      button.innerHTML = `<span class="btn-caption">${text}</span><i class="ph ph-arrow-right"></i>`;
    }

    return button;
  }

  updatePagination() {
    const pagination = document.getElementById('pagination');
    if (!pagination) return;

    const pageButtons = pagination.querySelectorAll('.blog-pagination-number');
    pageButtons.forEach(btn => {
      const pageNum = parseInt(btn.querySelector('.btn-caption').textContent);
      btn.classList.toggle('active', pageNum === this.currentPage);
    });

    const prevButton = pagination.querySelector('.prev');
    const nextButton = pagination.querySelector('.next');
    const totalPages = Math.ceil(this.filteredProducts.length / this.cardsPerPage);

    if (prevButton) prevButton.classList.toggle('disabled', this.currentPage === 1);
    if (nextButton) nextButton.classList.toggle('disabled', this.currentPage === totalPages);
  }

  initSearch() {
    const searchInput = document.querySelector('.filter-search__input');
    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();

      if (query === '') {
        // Сбрасываем на отфильтрованные по категории продукты
        if (this.currentCategory) {
          this.filteredProducts = this.allProducts.filter(product => {
            return product.category && product.category.slug === this.currentCategory;
          });
        } else {
          this.filteredProducts = [...this.allProducts];
        }
      } else {
        // Ищем среди уже отфильтрованных по категории продуктов
        const categoryFiltered = this.currentCategory
          ? this.allProducts.filter(product => {
              return product.category && product.category.slug === this.currentCategory;
            })
          : this.allProducts;

        this.filteredProducts = categoryFiltered.filter(product => {
          const title = (product.title || product.name || '').toLowerCase();
          return title.includes(query);
        });
      }

      this.currentPage = 1;
      this.renderCards();
      this.createPagination();
    });
  }

  scrollToTop() {
    const header = document.getElementById('header');
    const headerHeight = header ? header.offsetHeight : 0;
    const offset = 25;

    window.scrollTo({
      top: Math.max(0, headerHeight + offset),
      behavior: 'smooth'
    });
  }

  showLoader() {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = `<div class="loader-container"><div class="loader">${this.t('loading')}</div></div>`;
    }
  }

  hideLoader() {
    const loader = document.querySelector('.loader-container');
    if (loader) loader.remove();
  }

  showNoResults() {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = `<div class="no-results"><p>${this.t('noResults')}</p></div>`;
    }
    const pagination = document.getElementById('pagination');
    if (pagination) pagination.innerHTML = '';
  }

  showError(message) {
    const container = document.querySelector('.faw-truck-card-container');
    if (container) {
      container.innerHTML = `
        <div class="error-message">
          <p>${this.t('error')}: ${message}</p>
          <p>${this.t('tryAgain')}</p>
        </div>
      `;
    }
  }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
  new ProductsManager();
});