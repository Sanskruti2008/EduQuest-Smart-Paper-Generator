from database import get_supabase_client
client = get_supabase_client()
print(client.table('User').insert({'name': 'Test', 'role': 'faculty'}).execute().data)
