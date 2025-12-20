import os
import json
import glob
from datetime import datetime
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

def process_workout_request(request_file):
    """Process a single workout request file"""
    with open(request_file, 'r') as f:
        request = json.load(f)
    
    exercise_name = request.get('exercise')
    sets_data = request.get('sets', [])
    weight_type = request.get('weight_type', 'barbell')
    notes = request.get('notes', '')
    
    # Find exercise
    exercise = find_exercise(exercise_name)
    if not exercise:
        result = {
            'success': False,
            'error': f'Exercise "{exercise_name}" not found in database',
            'request_file': os.path.basename(request_file),
            'timestamp': datetime.now().isoformat()
        }
        return result
    
    exercise_id = exercise['id']
    
    # Create workout
    workout_result = supabase.table('workouts').insert({
        'date': datetime.now().isoformat(),
        'notes': notes
    }).execute()
    
    workout_id = workout_result.data[0]['workout_id']
    
    # Add sets
    sets_inserted = []
    for i, set_info in enumerate(sets_data, 1):
        set_data = {
            'workout_id': workout_id,
            'exercise_id': exercise_id,
            'weight': set_info.get('weight'),
            'reps': set_info.get('reps'),
            'set_number': i,
            'weight_type': weight_type,
            'date': datetime.now().isoformat()
        }
        
        set_result = supabase.table('sets').insert(set_data).execute()
        sets_inserted.append(set_result.data[0])
    
    # Calculate total volume
    total_volume = sum(s['weight'] * s['reps'] for s in sets_data if s.get('weight'))
    
    result = {
        'success': True,
        'workout_id': workout_id,
        'exercise': exercise_name,
        'sets_added': len(sets_inserted),
        'total_volume': total_volume,
        'request_file': os.path.basename(request_file),
        'timestamp': datetime.now().isoformat()
    }
    
    return result

def main():
    # Find all workout request files
    request_files = glob.glob('requests/workout_*.json')
    
    if not request_files:
        print("No workout requests found")
        return
    
    os.makedirs('results', exist_ok=True)
    
    for request_file in request_files:
        print(f"\nProcessing: {request_file}")
        result = process_workout_request(request_file)
        
        # Save result
        result_filename = request_file.replace('requests/', 'results/').replace('.json', '_result.json')
        with open(result_filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        if result['success']:
            print(f"✅ SUCCESS: Added {result['sets_added']} sets for {result['exercise']}")
            print(f"   Total volume: {result['total_volume']} lbs")
        else:
            print(f"❌ ERROR: {result['error']}")
        
        # Delete the request file after processing
        os.remove(request_file)
        print(f"   Deleted request file: {request_file}")

if __name__ == '__main__':
    main()
