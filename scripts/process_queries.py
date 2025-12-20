import os
import json
import glob
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def find_exercise(exercise_name):
    """Find exercise by name (case-insensitive)"""
    result = supabase.table('exercises').select('*').ilike('name', exercise_name).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None

def query_max_weight(exercise_name, days_back):
    """Get max weight progression for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    exercise = find_exercise(exercise_name)
    if not exercise:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise['id']
    
    # Query sets
    result = supabase.table('sets').select('date, weight, reps').eq('exercise_id', exercise_id).gte('date', cutoff_date).order('date').execute()
    
    # Group by date and find max
    daily_max = {}
    for set_record in result.data:
        date_key = set_record['date'][:10]  # Just the date part
        if date_key not in daily_max or (set_record['weight'] and set_record['weight'] > daily_max[date_key]['weight']):
            daily_max[date_key] = {
                'date': date_key,
                'weight': set_record['weight'],
                'reps': set_record['reps']
            }
    
    return {
        'exercise': exercise_name,
        'query_type': 'max_weight',
        'days_back': days_back,
        'data': sorted(daily_max.values(), key=lambda x: x['date'])
    }

def query_volume(exercise_name, days_back):
    """Calculate total volume for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    exercise = find_exercise(exercise_name)
    if not exercise:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise['id']
    
    result = supabase.table('sets').select('weight, reps, date').eq('exercise_id', exercise_id).gte('date', cutoff_date).execute()
    
    total_volume = sum(set_record['weight'] * set_record['reps'] for set_record in result.data if set_record.get('weight'))
    
    # Group by week for weekly breakdown
    weekly_volume = {}
    for set_record in result.data:
        if not set_record.get('weight'):
            continue
        date_obj = datetime.fromisoformat(set_record['date'].replace('Z', '+00:00'))
        week_key = date_obj.strftime('%Y-W%U')
        if week_key not in weekly_volume:
            weekly_volume[week_key] = 0
        weekly_volume[week_key] += set_record['weight'] * set_record['reps']
    
    return {
        'exercise': exercise_name,
        'query_type': 'volume',
        'days_back': days_back,
        'total_volume': total_volume,
        'total_sets': len(result.data),
        'weekly_breakdown': [{'week': k, 'volume': v} for k, v in sorted(weekly_volume.items())]
    }

def query_history(exercise_name, days_back):
    """Get complete workout history for an exercise"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    exercise = find_exercise(exercise_name)
    if not exercise:
        return {'error': f'Exercise "{exercise_name}" not found'}
    
    exercise_id = exercise['id']
    
    result = supabase.table('sets').select('*').eq('exercise_id', exercise_id).gte('date', cutoff_date).order('date', desc=True).execute()
    
    return {
        'exercise': exercise_name,
        'query_type': 'history',
        'days_back': days_back,
        'total_sets': len(result.data),
        'data': result.data
    }

def query_recent_workouts(days_back):
    """Get all recent workouts across all exercises"""
    cutoff_date = (datetime.now() - timedelta(days=int(days_back))).isoformat()
    
    # Get workouts with their sets
    workouts = supabase.table('workouts').select('*, sets(*, exercises(*))').gte('date', cutoff_date).order('date', desc=True).execute()
    
    return {
        'query_type': 'recent_workouts',
        'days_back': days_back,
        'total_workouts': len(workouts.data),
        'data': workouts.data
    }

def process_query_request(request_file):
    """Process a single query request file"""
    with open(request_file, 'r') as f:
        request = json.load(f)
    
    query_type = request.get('query_type')
    exercise_name = request.get('exercise', '')
    days_back = request.get('days_back', 90)
    
    if query_type == 'max_weight':
        result = query_max_weight(exercise_name, days_back)
    elif query_type == 'volume':
        result = query_volume(exercise_name, days_back)
    elif query_type == 'history':
        result = query_history(exercise_name, days_back)
    elif query_type == 'recent_workouts':
        result = query_recent_workouts(days_back)
    else:
        result = {'error': f'Unknown query type: {query_type}'}
    
    result['request_file'] = os.path.basename(request_file)
    result['timestamp'] = datetime.now().isoformat()
    
    return result

def main():
    # Find all query request files
    request_files = glob.glob('requests/query_*.json')
    
    if not request_files:
        print("No query requests found")
        return
    
    os.makedirs('results', exist_ok=True)
    
    for request_file in request_files:
        print(f"\nProcessing: {request_file}")
        result = process_query_request(request_file)
        
        # Save result
        result_filename = request_file.replace('requests/', 'results/').replace('.json', '_result.json')
        with open(result_filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
        else:
            print(f"✅ SUCCESS: Query completed")
            if 'data' in result:
                print(f"   Returned {len(result.get('data', []))} records")
        
        # Delete the request file after processing
        os.remove(request_file)
        print(f"   Deleted request file: {request_file}")

if __name__ == '__main__':
    main()
