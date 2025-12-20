import os
import json
from datetime import datetime
from supabase import create_client, Client

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def find_or_create_exercise(exercise_name):
    """Find exercise by name or return None if not found"""
    # Search for exercise (case-insensitive)
    result = supabase.table('exercises').select('*').ilike('name', exercise_name).execute()
    
    if result.data and len(result.data) > 0:
        return result.data[0]['id']
    else:
        return None

def add_workout():
    exercise_name = os.environ.get('EXERCISE_NAME')
    sets_data_str = os.environ.get('SETS_DATA')
    weight_type = os.environ.get('WEIGHT_TYPE', 'barbell')
    notes = os.environ.get('NOTES', '')
    
    # Parse sets data
    sets_data = json.loads(sets_data_str)
    
    # Find exercise
    exercise_id = find_or_create_exercise(exercise_name)
    
    if not exercise_id:
        result = {
            'success': False,
            'error': f'Exercise "{exercise_name}" not found in database. Please add it first.',
            'timestamp': datetime.now().isoformat()
        }
        with open('results/latest.json', 'w') as f:
            json.dump(result, f, indent=2)
        return
    
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
    
    # Save result
    result = {
        'success': True,
        'workout_id': workout_id,
        'exercise': exercise_name,
        'sets_added': len(sets_inserted),
        'timestamp': datetime.now().isoformat()
    }
    
    os.makedirs('results', exist_ok=True)
    with open('results/latest.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Added {len(sets_inserted)} sets for {exercise_name}")
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    add_workout()
