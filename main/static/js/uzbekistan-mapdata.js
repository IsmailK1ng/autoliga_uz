var simplemaps_countrymap_mapdata = {
  main_settings: {
    // Umumiy sozlamalar
    width: "responsive",
    background_color: "#FFFFFF",
    background_transparent: "yes",
    border_color: "#ffffff",
    pop_ups: "no", // O'zimizning panelimiz chiqishi uchun buni "no" qilamiz
    
    // Viloyat ranglari
    state_description: "",
    state_color: "#f3f3f3",
    state_hover_color: "#f66e2e",
    state_url: "",
    border_size: 1.5,
    all_states_inactive: "no",
    all_states_zoomable: "yes",

    // Yozuvlar (Labe) sozlamalari
    label_color: "#ffffff",
    label_hover_color: "#ffffff",
    label_size: 16,
    label_font: "Arial",
    label_display: "auto",
    label_scale: "yes",
    hide_labels: "no",
   
    // Zoom sozlamalari
    zoom: "yes",
    manual_zoom: "yes",
    back_image: "no",
    initial_zoom: "-1",
    region_opacity: 1,
    region_hover_opacity: 0.6,
    zoom_out_incrementally: "yes",
    zoom_percentage: 0.99,
    zoom_time: 0.5,
    
    // Popup sozlamalari (Simplemaps o'ziniki)
    popup_color: "white",
    popup_opacity: 0.9,
    popup_shadow: 1,
    popup_corners: 5,
    popup_font: "12px/1.5 Verdana, Arial, Helvetica, sans-serif",
    
    // Advanced
    div: "map",
    auto_load: "yes",
    url_new_tab: "no",
    fade_time: 0.1
  },

  state_specific: {
    UZAN: { name: "Andijon" },
    UZBU: { name: "Bukhoro" },
    UZFA: { name: "Ferghana" },
    UZJI: { name: "Jizzakh" },
    UZNG: { name: "Namangan" },
    UZNW: { name: "Navoi" },
    UZQA: { name: "Kashkadarya" },
    UZQR: { name: "Karakalpakstan" },
    UZSA: { name: "Samarkand" },
    UZSI: { name: "Sirdaryo" },
    UZSU: { name: "Surkhandarya" },
    UZTO: { name: "Toshkent viloyati" },
    UZTK: { name: "Toshkent shahri" },
    UZXO: { name: "Khorezm" }
  },

  locations: {},

  labels: {
    UZAN: { name: "Andijon", parent_id: "UZAN" },
    UZBU: { name: "Bukhoro", parent_id: "UZBU" },
    UZFA: { name: "Ferghana", parent_id: "UZFA" },
    UZJI: { name: "Jizzakh", parent_id: "UZJI" },
    UZNG: { name: "Namangan", parent_id: "UZNG" },
    UZNW: { name: "Navoi", parent_id: "UZNW" },
    UZQA: { name: "Kashkadarya", parent_id: "UZQA" },
    UZQR: { name: "Karakalpakstan", parent_id: "UZQR" },
    UZSA: { name: "Samarkand", parent_id: "UZSA" },
    UZSI: { name: "Sirdaryo", parent_id: "UZSI" },
    UZSU: { name: "Surkhandarya", parent_id: "UZSU" },
    UZTO: { name: "Toshkent viloyati", parent_id: "UZTO" },
    UZTK: { name: "Toshkent shahri", parent_id: "UZTK" },
    UZXO: { name: "Khorezm", parent_id: "UZXO" }
  }
};