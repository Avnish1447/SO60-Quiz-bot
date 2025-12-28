"""
Helper functions for building group selection keyboards.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config
import json


def build_group_selection_keyboard():
    """Build keyboard for selecting target groups."""
    keyboard = []
    
    # Add button for each configured group as checkboxes
    for group_key, group_info in config.GROUP_CONFIGS.items():
        group_name = group_info['name']
        keyboard.append([
            InlineKeyboardButton(
                f"☐ {group_name}", 
                callback_data=f"group_toggle_{group_key}"
            )
        ])
    
    # Add "Select All" and "Confirm" buttons
    keyboard.append([InlineKeyboardButton("📊 Select All Groups", callback_data="group_select_all")])
    keyboard.append([InlineKeyboardButton("✅ Confirm Selection", callback_data="group_confirm")])
    
    return InlineKeyboardMarkup(keyboard)


def update_group_selection_keyboard(selected_groups):
    """Update keyboard to show current selection state."""
    keyboard = []
    
    # Add button for each configured group with checkmark if selected
    for group_key, group_info in config.GROUP_CONFIGS.items():
        group_name = group_info['name']
        is_selected = group_key in selected_groups
        checkbox = "☑️" if is_selected else "☐"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{checkbox} {group_name}", 
                callback_data=f"group_toggle_{group_key}"
            )
        ])
    
    # Add "Select All" and "Confirm" buttons
    all_selected = len(selected_groups) == len(config.GROUP_CONFIGS)
    select_all_text = "📊 Select All Groups" if not all_selected else "🔲 Deselect All"
    
    keyboard.append([InlineKeyboardButton(select_all_text, callback_data="group_select_all")])
    keyboard.append([InlineKeyboardButton("✅ Confirm Selection", callback_data="group_confirm")])
    
    return InlineKeyboardMarkup(keyboard)


def format_selected_groups_text(selected_groups):
    """Format text showing which groups are selected."""
    if not selected_groups:
        return "⚠️ No groups selected!"
    
    if len(selected_groups) == len(config.GROUP_CONFIGS):
        return "📊 **All Groups Selected**"
    
    group_names = [config.GROUP_CONFIGS[gid]['name'] for gid in selected_groups]
    return "**Selected Groups:**\n" + "\n".join(f"✓ {name}" for name in group_names)
