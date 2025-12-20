import os
import json
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def query_max_weight(exercise_name, days_back):
    """Get max weight progression for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    # Get exercise ID
    exercise_result = supabase.table('exercises').select('id').ilike('name', exercise_name).execute()
    if not exercise_result.data:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise_result.data[0]['id']
    
    # Query sets with max weight per day
    result = supabase.table('sets').select('date, weight, reps').eq('exercise_id', exercise_id).gte('date', cutoff_date).order('date').execute()
    
    # Group by date and find max
    daily_max = {}
    for set_record in result.data:
        date_key = set_record['date'][:10]  # Just the date part
        if date_key not in daily_max or set_record['weight'] > daily_max[date_key]['weight']:
            daily_max[date_key] = {
                'date': date_key,
                'weight': set_record['weight'],
                'reps': set_record['reps']
            }
    
    return {
        'exercise': exercise_name,
        'query_type': 'max_weight',
        'days_back': days_back,
        'data': list(daily_max.values())
    }

def query_volume(exercise_name, days_back):
    """Calculate total volume for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    exercise_result = supabase.table('exercises').select('id').ilike('name', exercise_name).execute()
    if not exercise_result.data:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise_result.data[0]['id']
    
    result = supabase.table('sets').select('weight, reps, date').eq('exercise_id', exercise_id).gte('date', cutoff_date).execute()
    
    total_volume = sum(set_record['weight'] * set_record['reps'] for set_record in result.data if set_record['weight'])
    
    return {
        'exercise': exercise_name,
        'query_type': 'volume',
        'days_back': days_back,
        'total_volume': total_volume,
        'total_sets': len(result.data)
    }

def query_history(exercise_name, days_back):
    """Get complete workout history for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    exercise_result = supabase.table('exercises').select('id').ilike('name', exercise_name).execute()
    if not exercise_result.data:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise_result.data[0]['id']
    
    result = supabase.table('sets').select('*').eq('exercise_id', exercise_id).gte('date', cutoff_date).order('date', desc=True).execute()
    
    return {
        'exercise': exercise_name,
        'query_type': 'history',
        'days_back': days_back,
        'data': result.data
    }

def main():
    query_type = os.environ.get('QUERY_TYPE')
    exercise_name = os.environ.get('EXERCISE_NAME', '')
    days_back = os.environ.get('DAYS_BACK', '90')
    
    if query_type == 'max_weight':
        result = query_max_weight(exercise_name, days_back)
    elif query_type == 'volume':
        result = query_volume(exercise_name, days_back)
    elif query_type == 'history':
        result = query_history(exercise_name, days_back)
    else:
        result = {'error': f'Unknown query type: {query_type}'}
    
    os.makedirs('results', exist_ok=True)
    with open('results/query_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
