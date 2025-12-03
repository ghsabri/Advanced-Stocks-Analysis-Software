# CUSTOM VIEWS PERSISTENCE - DEPLOYMENT GUIDE

**Date:** November 21, 2025  
**Feature:** Custom views saved to database + Default to Performance view  
**Status:** Ready for deployment

---

## ✅ WHAT THIS ADDS:

1. **Custom views persist** - User-created views saved to database
2. **View preferences persist** - Which view is selected for each watchlist
3. **Default to Performance** - New watchlists start with Performance view
4. **Survives refresh** - All custom views and selections load from database

---

## 📥 FILES TO DEPLOY:

### **File 1: database.py**
📥 Download: [database_WITH_CUSTOM_VIEWS.py](computer:///mnt/user-data/outputs/database_WITH_CUSTOM_VIEWS.py)  
📍 Deploy to: `src/database.py`

### **File 2: Watchlists page**
📥 Download: [3_Watchlists_FINAL_WITH_CUSTOM_VIEWS.py](computer:///mnt/user-data/outputs/3_Watchlists_FINAL_WITH_CUSTOM_VIEWS.py)  
📍 Deploy to: `pages/3_Watchlists.py`

---

## 🚀 DEPLOYMENT STEPS:

### Step 1: Stop Streamlit
```bash
# Press Ctrl+C in terminal
```

### Step 2: Deploy files
```bash
cd C:\Work\Stock_Analysis_Project\mj-stocks-analysis

# Deploy database.py
copy database_WITH_CUSTOM_VIEWS.py src\database.py

# Deploy Watchlists page  
copy 3_Watchlists_FINAL_WITH_CUSTOM_VIEWS.py pages\3_Watchlists.py
```

### Step 3: Restart Streamlit
```bash
streamlit run Home.py
```

---

## 🧪 TESTING CHECKLIST:

### Test 1: Default View is Performance
- [ ] Create a new watchlist
- [ ] Should automatically show "Performance" view
- [ ] Columns: Symbol, Price, Change %, 1M/3M/YTD Perf%, 52W High/Low

### Test 2: Create Custom View
- [ ] Click "Manage Custom Views"
- [ ] Create new view: "My View"
- [ ] Select some columns
- [ ] Click "Save View"
- [ ] Terminal should show: "✅ Saved custom view: My View"

### Test 3: Custom View Persists
- [ ] Refresh browser (F5)
- [ ] Go to Watchlists
- [ ] Check view dropdown - "My View" should be there! ✅
- [ ] Select "My View" - columns should match what you created

### Test 4: View Selection Persists
- [ ] Select "Technical" view for watchlist
- [ ] Refresh browser
- [ ] Go back to that watchlist
- [ ] Should still show "Technical" view ✅

### Test 5: Restart App
- [ ] Stop Streamlit (Ctrl+C)
- [ ] Start again
- [ ] Custom views should load from database
- [ ] Terminal should show: "📋 Loaded X custom views"

---

## 📊 VERIFY IN SUPABASE:

1. Go to: https://supabase.com/dashboard
2. Open your project
3. Click "Table Editor"
4. Check `user_preferences` table
5. Should see rows with:
   - `preference_type` = 'custom_view' (your custom views)
   - `preference_type` = 'watchlist_view_pref' (view selections)

---

## 🎯 EXPECTED TERMINAL OUTPUT:

### On Startup:
```
✅ Database module loaded successfully
📂 Loading watchlists from database...
✅ Loaded X watchlists from database
📋 Loaded X custom views
```

### When Creating Custom View:
```
✅ Saved custom view: My Trading View
✅ Saved view preference for watchlist 1: My Trading View
```

### When Changing View:
```
✅ Saved view preference for watchlist 1: Performance
```

---

## 🔄 IF SOMETHING GOES WRONG:

### Rollback:
```bash
copy pages\3_Watchlists_BEFORE_CUSTOM_VIEWS.py pages\3_Watchlists.py
copy src\database_BEFORE_CUSTOM_VIEWS.py src\database.py
streamlit run Home.py
```

---

## 🎉 WHAT YOU GET:

✅ **Custom views persist** - Create once, use forever  
✅ **View preferences persist** - Each watchlist remembers its view  
✅ **Performance default** - New watchlists start with best view for traders  
✅ **Professional UX** - Settings don't disappear on refresh  
✅ **Beta ready** - Testers can customize and keep their views  

---

## 📋 CHANGES SUMMARY:

### database.py:
- Added `save_custom_view()` - Save custom view to database
- Added `get_all_custom_views()` - Load all custom views
- Added `delete_custom_view()` - Delete a custom view
- Added `save_watchlist_view_preference()` - Save which view is selected
- Added `get_watchlist_view_preference()` - Load view selection

### 3_Watchlists.py:
- Changed default from "Standard" to "Performance"
- Load custom views from database on startup
- Save custom views to database when created
- Save view preferences when changed
- Load view preferences for each watchlist

---

**Ready to deploy! Download the files and follow the steps above.**
