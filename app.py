import gradio as gr
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
import math

class Player:
    def __init__(self, name, gender, skill_level):
        self.name = name
        self.gender = gender  # 'M' or 'F'
        self.skill_level = skill_level  # 'Amateur' or 'Advanced'
        self.matches = []

class Team:
    def __init__(self, id, category, players):
        self.id = id
        self.group_id = None
        self.category = category
        self.players = players
        self.matches = []
        self.group_number = None
    
    def __str__(self):
        return f"Team {self.group_number}"

class Match:
    def __init__(self, team1, team2, group_id, round_num, category):
        self.team1 = team1
        self.team2 = team2
        self.group_id = group_id
        self.round_num = round_num
        self.court = None
        self.start_time = None
        self.category = category
    
    def __str__(self):
        time_str = self.start_time.strftime("%H:%M") if self.start_time else "TBD"
        return f"[{time_str}] Court {self.court}: {self.category} Group {self.group_id} - {self.team1} vs {self.team2}"

def generate_matches_for_group(teams, category, group_id, qualifying_teams):
    """Generate round-robin matches for a group of teams"""
    matches = []
    teams_in_group = [team for team in teams if team.group_id == group_id]
    
    if len(teams_in_group) < 2:
        return matches
    
    # Generate round-robin matches
    for i in range(len(teams_in_group)):
        for j in range(i + 1, len(teams_in_group)):
            team1 = teams_in_group[i]
            team2 = teams_in_group[j]
            match = Match(
                category=category,
                team1=team1,
                team2=team2,
                group_id=group_id,
                round_num=len(matches) + 1
            )
            matches.append(match)
    
    return matches

def generate_round_robin_matches(teams, group_id):
    """Generate round-robin matches for a group of teams"""
    matches = []
    n = len(teams)
    
    if n < 2:
        return matches
    
    # If odd number of teams, add a dummy team for byes
    if n % 2:
        teams = teams + [None]
        n += 1
    
    for round_num in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            team1 = teams[i]
            team2 = teams[n - 1 - i]
            
            # Skip matches with dummy team (byes)
            if team1 is not None and team2 is not None:
                match = Match(team1, team2, group_id, round_num + 1, team1.category)
                round_matches.append(match)
        
        # Rotate teams for next round: fix team[0], rotate others clockwise
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]
        matches.extend(round_matches)
    
    return matches

def schedule_matches(matches, start_time, end_time, match_duration, courts_available, keep_categories_separate=False, category_priority=None):
    """Schedule matches across available courts and time slots"""
    if not matches:
        return []
    
    # Convert times to datetime
    current_date = datetime.now().date()
    current_time = datetime.combine(current_date, datetime.strptime(start_time, "%H:%M").time())
    end_time = datetime.combine(current_date, datetime.strptime(end_time, "%H:%M").time())
    match_duration_delta = timedelta(minutes=match_duration)
    
    # Create time slots for the day
    time_slots = []
    current = current_time
    while current + match_duration_delta <= end_time:
        time_slots.append(current)
        current += match_duration_delta
    
    scheduled_matches = []
    unscheduled_matches = matches.copy()
    
    # Initialize court availability tracking
    court_slots = {court: {slot: None for slot in time_slots} for court in range(1, courts_available + 1)}
    
    # Get unique categories and sort by priority (lower number = higher priority)
    categories = sorted(set(match.category for match in matches))
    if category_priority:
        priority_map = {cat: priority for cat, priority in category_priority.items()}
        categories.sort(key=lambda x: priority_map.get(x, 999))  # Lower numbers first
    
    if keep_categories_separate:
        current_slot_idx = 0
        while unscheduled_matches and current_slot_idx < len(time_slots):
            time_slot = time_slots[current_slot_idx]
            available_courts = list(range(1, courts_available + 1))
            matches_scheduled_this_slot = False
            
            # Try to schedule matches from each category in this time slot
            for category in categories:
                if not available_courts:
                    break
                    
                # Get matches for this category, sorted by group and round
                category_matches = sorted(
                    [m for m in unscheduled_matches if m.category == category],
                    key=lambda x: (x.group_id, x.round_num)
                )
                
                # Try to schedule each match in this category
                for match in category_matches[:]:  # Create a copy to avoid modification during iteration
                    if not available_courts:
                        break
                    
                    court = available_courts[0]
                    match.start_time = time_slot
                    match.court = court
                    court_slots[court][time_slot] = match
                    scheduled_matches.append(match)
                    unscheduled_matches.remove(match)
                    available_courts.pop(0)
                    matches_scheduled_this_slot = True
            
            # Move to next time slot if we scheduled something or no courts were available
            if matches_scheduled_this_slot or not available_courts:
                current_slot_idx += 1
    else:
        current_slot_idx = 0
        while unscheduled_matches and current_slot_idx < len(time_slots):
            time_slot = time_slots[current_slot_idx]
            available_courts = list(range(1, courts_available + 1))
            matches_scheduled_this_slot = False
            
            # Get all matches sorted by priority (lower = higher priority), group, and round
            sorted_matches = sorted(
                unscheduled_matches,
                key=lambda x: (category_priority.get(x.category, 999), x.group_id, x.round_num)
            )
            
            # Schedule as many matches as possible in current time slot
            for match in sorted_matches[:]:  # Create a copy to avoid modification during iteration
                if not available_courts:
                    break
                
                court = available_courts[0]
                match.start_time = time_slot
                match.court = court
                court_slots[court][time_slot] = match
                scheduled_matches.append(match)
                unscheduled_matches.remove(match)
                available_courts.pop(0)
                matches_scheduled_this_slot = True
            
            # Move to next time slot if we scheduled something or no courts were available
            if matches_scheduled_this_slot or not available_courts:
                current_slot_idx += 1
    
    # Sort matches by start time and court number
    scheduled_matches.sort(key=lambda x: (x.start_time, x.court))
    
    # Calculate and print court utilization statistics
    total_slots = len(time_slots) * courts_available
    used_slots = sum(1 for court in court_slots.values() for slot in court.values() if slot is not None)
    utilization = (used_slots / total_slots) * 100
    print(f"Court utilization: {utilization:.1f}%")
    
    if unscheduled_matches:
        print(f"Warning: {len(unscheduled_matches)} matches could not be scheduled")
        for match in unscheduled_matches:
            print(f"- Unscheduled: {match.category} Group {match.group_id} Round {match.round_num}")
    
    return scheduled_matches

def create_teams_for_category(category, total_participants, amateur_ratio, women_advanced_ratio, plus_35_ratio, parent_child_ratio, teams_per_group):
    """Create teams for a specific category"""
    # Calculate player distributions
    total_amateur = int(total_participants * amateur_ratio)
    total_advanced = total_participants - total_amateur
    advanced_women = int(total_advanced * women_advanced_ratio)
    advanced_men = total_advanced - advanced_women
    
    teams = []
    
    if category == "Men's Doubles":
        # Create teams with advanced men players
        players = [Player(f"M{i+1}", "M", "Advanced") for i in range(advanced_men)]
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                team = Team(len(teams) + 1, category, [players[i], players[i+1]])
                teams.append(team)
    
    elif category == "Mixed Doubles":
        # Create mixed doubles teams (one man + one woman)
        men = [Player(f"M{i+1}", "M", "Advanced") for i in range(advanced_men)]
        women = [Player(f"W{i+1}", "F", "Advanced") for i in range(advanced_women)]
        min_pairs = min(len(men), len(women))
        for i in range(min_pairs):
            team = Team(len(teams) + 1, category, [men[i], women[i]])
            teams.append(team)
    
    elif category == "Amateur":
        # Create amateur teams, excluding those reserved for parent-child
        parent_child_players = int(total_amateur * parent_child_ratio)
        available_amateurs = total_amateur - parent_child_players
        players = [Player(f"A{i+1}", "M" if i % 2 == 0 else "F", "Amateur") 
                  for i in range(available_amateurs)]
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                team = Team(len(teams) + 1, category, [players[i], players[i+1]])
                teams.append(team)
    
    elif category == "35+":
        # Use a subset of advanced players for 35+
        players = ([Player(f"M{i+1}", "M", "Advanced") for i in range(int(advanced_men * plus_35_ratio))] +
                  [Player(f"W{i+1}", "F", "Advanced") for i in range(int(advanced_women * plus_35_ratio))])
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                team = Team(len(teams) + 1, category, [players[i], players[i+1]])
                teams.append(team)
    
    elif category == "Open":
        # Create teams with any advanced players not used in 35+
        non_35_ratio = 1 - plus_35_ratio
        players = ([Player(f"M{i+1}", "M", "Advanced") for i in range(int(advanced_men * non_35_ratio))] +
                  [Player(f"W{i+1}", "F", "Advanced") for i in range(int(advanced_women * non_35_ratio))])
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                team = Team(len(teams) + 1, category, [players[i], players[i+1]])
                teams.append(team)
    
    elif category == "Parent-Child":
        # Calculate number of parent-child pairs
        num_pairs = int((total_amateur * parent_child_ratio) / 2)  # Divide by 2 as each team needs one parent and one child
        
        # Create parent-child teams
        for i in range(num_pairs):
            child = Player(f"Child{i+1}", "M" if i % 2 == 0 else "F", "Amateur")
            parent = Player(f"Parent{i+1}", "M" if i % 2 == 0 else "F", "Advanced")
            team = Team(len(teams) + 1, category, [parent, child])
            teams.append(team)
    
    # Distribute teams into groups
    if teams:
        num_teams = len(teams)
        if num_teams < teams_per_group:
            # If we have fewer teams than the minimum group size, put them all in one group
            for team in teams:
                team.group_id = 1
        else:
            # Calculate number of groups needed
            num_groups = max(1, (num_teams + teams_per_group - 1) // teams_per_group)
            teams_per_actual_group = num_teams // num_groups
            remainder = num_teams % num_groups
            
            current_group = 1
            teams_in_current_group = 0
            target_teams_in_group = teams_per_actual_group + (1 if current_group <= remainder else 0)
            
            for team in teams:
                if teams_in_current_group >= target_teams_in_group:
                    current_group += 1
                    teams_in_current_group = 0
                    target_teams_in_group = teams_per_actual_group + (1 if current_group <= remainder else 0)
                
                team.group_id = current_group
                teams_in_current_group += 1
    
    return teams

def calculate_groups_and_matches(total_participants, amateur_ratio, women_advanced_ratio, plus_35_ratio, parent_child_ratio, enabled_categories, teams_per_group_settings, qualifying_teams):
    """Calculate groups and generate matches for enabled categories"""
    all_teams = {}
    all_matches = []
    group_info = {
        'Player Distribution': {
            'Total': total_participants,
            'Amateur': int(total_participants * amateur_ratio),
            'Advanced Men': int((total_participants - int(total_participants * amateur_ratio)) * (1 - women_advanced_ratio)),
            'Advanced Women': int((total_participants - int(total_participants * amateur_ratio)) * women_advanced_ratio),
            '35+ Players': int((total_participants - int(total_participants * amateur_ratio)) * plus_35_ratio),
            'Parent-Child Teams': int(total_participants * amateur_ratio * parent_child_ratio / 2)
        },
        'Total Matches': 0,
        'Men\'s Doubles Groups': 0,
        'Mixed Doubles Groups': 0,
        'Amateur Groups': 0,
        '35+ Groups': 0,
        'Open Groups': 0,
        'Parent-Child Groups': 0
    }
    
    for category in enabled_categories:
        teams = create_teams_for_category(category, total_participants, amateur_ratio, women_advanced_ratio, plus_35_ratio, parent_child_ratio, teams_per_group_settings[category])
        if teams:
            all_teams[category] = teams
            
            # Count groups for this category
            num_groups = max(team.group_id for team in teams)
            if category == "Men's Doubles":
                group_info['Men\'s Doubles Groups'] = num_groups
            elif category == "Mixed Doubles":
                group_info['Mixed Doubles Groups'] = num_groups
            elif category == "Amateur":
                group_info['Amateur Groups'] = num_groups
            elif category == "35+":
                group_info['35+ Groups'] = num_groups
            elif category == "Open":
                group_info['Open Groups'] = num_groups
            elif category == "Parent-Child":
                group_info['Parent-Child Groups'] = num_groups
            
            # Generate matches for each group
            for group_id in range(1, num_groups + 1):
                group_matches = generate_matches_for_group(teams, category, group_id, qualifying_teams)
                all_matches.extend(group_matches)
    
    group_info['Total Matches'] = len(all_matches)
    
    return all_matches, all_teams, group_info

def calculate_available_match_slots(start_time, end_time, match_duration, courts_available):
    # Convert times to datetime
    current_date = datetime.now().date()
    start_datetime = datetime.combine(current_date, datetime.strptime(start_time, "%H:%M").time())
    end_datetime = datetime.combine(current_date, datetime.strptime(end_time, "%H:%M").time())
    
    # Calculate total minutes available
    total_minutes = (end_datetime - start_datetime).total_seconds() / 60
    
    # Calculate how many match slots are available per court
    matches_per_court = int(total_minutes / match_duration)
    
    # Total available match slots across all courts
    total_available_slots = matches_per_court * courts_available
    
    return total_available_slots

def create_schedule_display(scheduled_matches, all_teams, group_info, enabled_categories):
    if not scheduled_matches:
        return "No matches could be scheduled within the given time constraints."
    
    # Create tournament summary box
    summary = """
<div style='border:1px solid var(--border-color-primary); padding:15px; border-radius:8px; margin-bottom:20px; background-color:var(--background-fill-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>
<h2 style='color:var(--body-text-color); margin-top:0'>🏆 Tournament Summary</h2>
<div style='display:grid; grid-template-columns:1fr 1fr; gap:20px'>
<div>
<h3 style='color:var(--body-text-color)'>📊 Player Distribution</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
<li>🏸 Total Participants: <b>{total}</b></li>
<li>👥 Amateur Players: <b>{amateur}</b></li>
<li>👨 Advanced Men: <b>{adv_men}</b></li>
<li>👩 Advanced Women: <b>{adv_women}</b></li>
<li>🎯 35+ Players: <b>{plus_35}</b></li>
<li>👨‍👦 Parent-Child Teams: <b>{parent_child}</b></li>
</ul>
</div>
<div>
<h3 style='color:var(--body-text-color)'>🏟️ Group Distribution</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
""".format(
        total=group_info['Player Distribution']['Total'],
        amateur=group_info['Player Distribution']['Amateur'],
        adv_men=group_info['Player Distribution']['Advanced Men'],
        adv_women=group_info['Player Distribution']['Advanced Women'],
        plus_35=group_info['Player Distribution']['35+ Players'],
        parent_child=group_info['Player Distribution']['Parent-Child Teams']
    )
    
    # Add group distribution for each category
    for category in enabled_categories:
        if category in all_teams:
            num_groups = len(set(team.group_id for team in all_teams[category]))
            teams_per_group = {i: len([t for t in all_teams[category] if t.group_id == i]) 
                             for i in range(1, num_groups + 1)}
            summary += f"<li>🎯 {category}: <b>{num_groups}</b> groups ("
            summary += ", ".join(f"G{g}: {n} teams" for g, n in teams_per_group.items())
            summary += ")</li>\n"
    
    summary += """
</ul>
</div>
</div>
</div>
"""
    
    # Create schedule table
    schedule = "<div style='margin-top:20px'><h2 style='color:var(--body-text-color)'>📅 Match Schedule</h2>"
    schedule += "<div style='overflow-x:auto'><table style='width:100%; border-collapse:collapse; margin-top:10px'>"
    schedule += "<tr style='background-color:var(--background-fill-primary)'>"
    schedule += "<th style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Time</th>"
    schedule += "<th style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Court</th>"
    schedule += "<th style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Category</th>"
    schedule += "<th style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Group</th>"
    schedule += "<th style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Match</th>"
    schedule += "</tr>"
    
    # Sort matches by time and court
    scheduled_matches.sort(key=lambda x: (x.start_time, x.court))
    
    current_time = None
    for match in scheduled_matches:
        time_str = match.start_time.strftime("%H:%M")
        
        # Add time separator
        if current_time != time_str:
            schedule += f"<tr style='background-color:var(--background-fill-secondary)'>"
            schedule += f"<td colspan='5' style='padding:5px; text-align:center; border:1px solid var(--border-color-primary); color:var(--body-text-color)'><b>{time_str}</b></td></tr>"
            current_time = time_str
        
        # Format team names
        team1_name = f"Team {match.team1.id}" if match.team1 else "TBD"
        team2_name = f"Team {match.team2.id}" if match.team2 else "TBD"
        
        schedule += "<tr>"
        schedule += f"<td style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>{time_str}</td>"
        schedule += f"<td style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Court {match.court}</td>"
        schedule += f"<td style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>{match.category}</td>"
        schedule += f"<td style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>Group {match.group_id}</td>"
        schedule += f"<td style='padding:10px; border:1px solid var(--border-color-primary); color:var(--body-text-color)'>{team1_name} vs {team2_name}</td>"
        schedule += "</tr>"
    
    schedule += "</table></div></div>"
    
    return summary + schedule

def create_tournament_schedule(
    total_participants,
    amateur_ratio,
    women_advanced_ratio,
    plus_35_ratio,
    parent_child_ratio,
    include_mens_doubles,
    include_mixed_doubles,
    include_amateur,
    include_35plus,
    include_open,
    include_parent_child,
    match_duration,
    mens_doubles_teams,
    mixed_doubles_teams,
    amateur_teams,
    plus_35_teams,
    open_teams,
    parent_child_teams,
    qualifying_teams,
    start_time,
    end_time,
    courts_available,
    keep_categories_separate,
    mens_doubles_priority,
    mixed_doubles_priority,
    amateur_priority,
    plus_35_priority,
    open_priority,
    parent_child_priority
):
    # Create list of enabled categories and their priorities
    enabled_categories = []
    category_priorities = {}
    
    if include_mens_doubles:
        enabled_categories.append("Men's Doubles")
        category_priorities["Men's Doubles"] = int(mens_doubles_priority)
    if include_mixed_doubles:
        enabled_categories.append("Mixed Doubles")
        category_priorities["Mixed Doubles"] = int(mixed_doubles_priority)
    if include_amateur:
        enabled_categories.append("Amateur")
        category_priorities["Amateur"] = int(amateur_priority)
    if include_35plus:
        enabled_categories.append("35+")
        category_priorities["35+"] = int(plus_35_priority)
    if include_open:
        enabled_categories.append("Open")
        category_priorities["Open"] = int(open_priority)
    if include_parent_child:
        enabled_categories.append("Parent-Child")
        category_priorities["Parent-Child"] = int(parent_child_priority)
    
    if not enabled_categories:
        return """
<div style='text-align: center; padding: 20px;'>
    <h2>⚠️ No Categories Selected</h2>
    <p>Please select at least one category to generate a schedule.</p>
</div>
"""
    
    # Calculate total available match slots
    total_slots = calculate_available_match_slots(start_time, end_time, match_duration, courts_available)
    
    # Generate matches and teams
    teams_per_group_settings = {
        "Men's Doubles": mens_doubles_teams,
        "Mixed Doubles": mixed_doubles_teams,
        "Amateur": amateur_teams,
        "35+": plus_35_teams,
        "Open": open_teams,
        "Parent-Child": parent_child_teams
    }
    all_matches, all_teams, group_info = calculate_groups_and_matches(
        total_participants, amateur_ratio, women_advanced_ratio, plus_35_ratio, parent_child_ratio,
        enabled_categories, teams_per_group_settings, qualifying_teams
    )
    
    if not all_matches:
        return """
<div style='text-align: center; padding: 20px;'>
    <h2>⚠️ No Matches Generated</h2>
    <p>Could not generate any matches with the current settings. Try adjusting the parameters.</p>
</div>
"""
    
    # Schedule matches with priorities
    scheduled_matches = schedule_matches(
        all_matches,
        start_time,
        end_time,
        match_duration,
        courts_available,
        keep_categories_separate,
        category_priorities
    )
    
    # Calculate scheduling statistics
    total_scheduled = len(scheduled_matches)
    total_matches = group_info["Total Matches"]
    scheduling_success_rate = (total_scheduled / total_matches * 100) if total_matches > 0 else 0
    court_utilization_rate = (total_scheduled / total_slots * 100) if total_slots > 0 else 0
    
    # Create configuration summary
    config_summary = f"""
<div style='border:1px solid var(--border-color-primary); padding:15px; border-radius:8px; margin-bottom:20px; background-color:var(--background-fill-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>
<h2 style='color:var(--body-text-color); margin-top:0'>⚙️ Tournament Configuration</h2>
<div style='display:grid; grid-template-columns:1fr 1fr; gap:20px'>
<div>
<h3 style='color:var(--body-text-color)'>📊 Basic Settings</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
<li>👥 Total Participants: <b>{total_participants}</b></li>
<li>🎾 Amateur Ratio: <b>{amateur_ratio * 100}%</b></li>
<li>👩 Women in Advanced: <b>{women_advanced_ratio * 100}%</b></li>
<li>⏱️ Match Duration: <b>{match_duration} minutes</b></li>
</ul>
</div>
<div>
<h3 style='color:var(--body-text-color)'>🏟️ Format Settings</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
<li>👥 Teams per Group:</li>
<ul style='list-style-type:none; padding-left:20px; color:var(--body-text-color)'>
<li>👨‍👨‍👦 Men's Doubles: <b>{mens_doubles_teams}</b></li>
<li>👫 Mixed Doubles: <b>{mixed_doubles_teams}</b></li>
<li>🎾 Amateur: <b>{amateur_teams}</b></li>
<li>🏆 35+: <b>{plus_35_teams}</b></li>
<li>🌟 Open: <b>{open_teams}</b></li>
<li>👪 Parent-Child: <b>{parent_child_teams}</b></li>
</ul>
<li>🏆 Qualifying Teams: <b>{qualifying_teams}</b></li>
<li>🏸 Courts Available: <b>{courts_available}</b></li>
<li>📅 Time: <b>{start_time}</b> to <b>{end_time}</b></li>
</ul>
</div>
</div>
</div>

<div style='border:1px solid var(--border-color-primary); padding:15px; border-radius:8px; margin-bottom:20px; background-color:var(--background-fill-primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1)'>
<h2 style='color:var(--body-text-color); margin-top:0'>📈 Schedule Statistics</h2>
<div style='display:grid; grid-template-columns:1fr 1fr; gap:20px'>
<div>
<h3 style='color:var(--body-text-color)'>🎯 Match Statistics</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
<li>📊 Required Matches: <b>{total_matches}</b></li>
<li>✅ Scheduled Matches: <b>{total_scheduled}</b></li>
<li>📈 Scheduling Success: <b>{scheduling_success_rate:.1f}%</b></li>
</ul>
</div>
<div>
<h3 style='color:var(--body-text-color)'>⏰ Time Slot Statistics</h3>
<ul style='list-style-type:none; padding-left:0; color:var(--body-text-color)'>
<li>🎯 Available Time Slots: <b>{total_slots}</b></li>
<li>📊 Court Utilization: <b>{court_utilization_rate:.1f}%</b></li>
<li>⚠️ Unscheduled Matches: <b>{total_matches - total_scheduled}</b></li>
</ul>
</div>
</div>
</div>
"""
    
    return config_summary + create_schedule_display(scheduled_matches, all_teams, group_info, enabled_categories)

def create_interface():
    with gr.Blocks(title="Tournament Schedule Generator") as demo:
        gr.Markdown("# 🏸 Tournament Schedule Generator")
        
        with gr.Row():
            with gr.Column():
                # Player Distribution
                gr.Markdown("### Player Distribution")
                total_participants = gr.Number(label="Total Participants", value=120, minimum=4)
                
                # Player Ratios
                gr.Markdown("#### Player Ratios")
                amateur_ratio = gr.Slider(label="Amateur Players Ratio", minimum=0, value=0.33, step=0.01)
                women_advanced_ratio = gr.Slider(label="Advanced Women Ratio (of Advanced Players)", minimum=0, value=0.33, step=0.01)
                plus_35_ratio = gr.Slider(label="35+ Players Ratio (of Advanced Players)", minimum=0, value=0.3, step=0.01)
                parent_child_ratio = gr.Slider(label="Parent-Child Teams Ratio (of Amateur Players)", minimum=0, value=0.3, step=0.01)
                
                # Category Selection, Priorities, and Group Settings
                gr.Markdown("### Categories and Group Settings")
                
                with gr.Row():
                    with gr.Column():
                        include_mens_doubles = gr.Checkbox(label="Men's Doubles", value=True)
                        mens_doubles_priority = gr.Number(label="Priority", value=1, minimum=1)
                        mens_doubles_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                with gr.Row():
                    with gr.Column():
                        include_mixed_doubles = gr.Checkbox(label="Mixed Doubles", value=True)
                        mixed_doubles_priority = gr.Number(label="Priority", value=2, minimum=1)
                        mixed_doubles_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                with gr.Row():
                    with gr.Column():
                        include_amateur = gr.Checkbox(label="Amateur", value=True)
                        amateur_priority = gr.Number(label="Priority", value=3, minimum=1)
                        amateur_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                with gr.Row():
                    with gr.Column():
                        include_35plus = gr.Checkbox(label="35+", value=True)
                        plus_35_priority = gr.Number(label="Priority", value=4, minimum=1)
                        plus_35_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                with gr.Row():
                    with gr.Column():
                        include_open = gr.Checkbox(label="Open", value=True)
                        open_priority = gr.Number(label="Priority", value=5, minimum=1)
                        open_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                with gr.Row():
                    with gr.Column():
                        include_parent_child = gr.Checkbox(label="Parent-Child", value=True)
                        parent_child_priority = gr.Number(label="Priority", value=6, minimum=1)
                        parent_child_teams = gr.Slider(label="Teams per Group", minimum=3, value=4, step=1)
                
                # Schedule Settings
                gr.Markdown("### Schedule Settings")
                match_duration = gr.Slider(label="Match Duration (minutes)", minimum=15, value=15, step=5)
                qualifying_teams = gr.Slider(label="Qualifying Teams", minimum=1, value=2, step=1)
                start_time = gr.Text(label="Start Time (HH:MM)", value="09:00")
                end_time = gr.Text(label="End Time (HH:MM)", value="18:00")
                courts_available = gr.Slider(label="Courts Available", minimum=1, value=4, step=1)
                keep_categories_separate = gr.Checkbox(label="Keep Categories Separate", value=True)
        
        # Output Display
        output_display = gr.HTML()
        
        # Submit Button
        gr.Button("Generate Schedule").click(
            fn=create_tournament_schedule,
            inputs=[
                total_participants,
                amateur_ratio,
                women_advanced_ratio,
                plus_35_ratio,
                parent_child_ratio,
                include_mens_doubles,
                include_mixed_doubles,
                include_amateur,
                include_35plus,
                include_open,
                include_parent_child,
                match_duration,
                mens_doubles_teams,
                mixed_doubles_teams,
                amateur_teams,
                plus_35_teams,
                open_teams,
                parent_child_teams,
                qualifying_teams,
                start_time,
                end_time,
                courts_available,
                keep_categories_separate,
                mens_doubles_priority,
                mixed_doubles_priority,
                amateur_priority,
                plus_35_priority,
                open_priority,
                parent_child_priority
            ],
            outputs=output_display
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=True)
