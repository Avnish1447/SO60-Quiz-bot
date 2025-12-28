# Database Migration Guide - Multi-Group Support

## ⚠️ IMPORTANT: Required for Upgrading to Multi-Group Version

If you're upgrading from the previous version of SO60 Quiz Bot, you **MUST** run the database migration before starting the bot with the new code.

---

## 🔄 What This Migration Does

The migration script will:
1. **Backup your existing database** (creates `quiz_bot.db.backup_YYYYMMDD_HHMMSS`)
2. **Add new columns:**
   - `target_groups` to `questions` table
   - `group_id` to `responses` table
3. **Create new table:**
   - `quiz_posts` for tracking polls per group
4. **Preserve all existing data** (backward compatible)

---

## 📋 Migration Steps

### **Step 1: Backup (Automatic)**
The script automatically creates a backup, but you can also manually backup:
```bash
copy quiz_bot.db quiz_bot.db.manual_backup
```

### **Step 2: Run Migration**
```bash
cd "path\to\SO60-Quiz-bot"
python database/migration_multigroup.py
```

### **Step 3: Verify Success**
You should see:
```
✅ Database migration completed successfully!
📊 Summary:
  - Added target_groups column to questions table
  - Added group_id column to responses table
  - Created quiz_posts table
  - Backup created at: quiz_bot.db.backup_YYYYMMDD_HHMMSS
```

### **Step 4: Update Configuration**
Add your groups to `.env`:
```bash
GROUP_CONFIGS=group1:Group Name:-1001234567890,group2:Another Group:-1009876543210
```

Use `get_chat_ids.py` to find your group chat IDs if needed.

### **Step 5: Start Bot**
```bash
python bot.py
```

---

## 🔙 Rollback (If Needed)

If something goes wrong:

1. **Stop the bot**
2. **Restore backup:**
   ```bash
   copy quiz_bot.db.backup_YYYYMMDD_HHMMSS quiz_bot.db
   ```
3. **Restart with old code**

---

## ✅ Verification Checklist

After migration and starting the bot:

- [ ] Bot starts without errors
- [ ] `/addquiz` shows group selection step
- [ ] Can post quiz to multiple groups
- [ ] Old quizzes still visible with `/viewquiz`
- [ ] Responses are being tracked
- [ ] `/sendleaderboard` works

---

## ❓ Troubleshooting

### "Table already has column"
This means you've already run the migration. It's safe to ignore.

### "Error: no such table: questions"
Your database might be corrupted. Restore from backup and try again.

### "Chat not found" when posting
Your `GROUP_CONFIGS` chat IDs are incorrect. Use `get_chat_ids.py` to find correct IDs.

---

## 📞 Support

If you encounter issues:
1. Check the backup was created successfully
2. Verify `.env` configuration
3. Review bot logs for specific errors
4. Restore from backup if needed

---

## 🎯 First-Time Setup (No Migration Needed)

If this is a fresh installation:
1. The database will be created automatically with the new schema
2. Just configure your `.env` with `GROUP_CONFIGS`
3. Run `python bot.py`

**No migration needed for new installations!**
