# Supabase Setup Guide for EduQuest.ai

## 🚀 Quick Start

Your EduQuest.ai project is now configured to use Supabase PostgreSQL instead of SQLite!

## 📋 Prerequisites

1. A Supabase account (free tier available at [supabase.com](https://supabase.com))
2. Python packages installed (run `pip install -r requirements.txt`)

## 🔧 Setup Steps

### Step 1: Create Supabase Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose your organization
4. Fill in:
   - **Project Name:** `eduquest-ai` (or any name you prefer)
   - **Database Password:** Create a strong password (save this!)
   - **Region:** Choose closest to your users
5. Click "Create new project" and wait ~2 minutes

### Step 2: Get Your Credentials

1. In your Supabase dashboard, click on your project
2. Go to **Settings** → **API**
3. Copy the following values:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **Project API keys** → **anon public** (starts with `eyJ...`)
   - **Project API keys** → **service_role** (starts with `eyJ...`) - *Keep this secret!*

### Step 3: Configure Environment Variables

1. In your `backend` folder, create/update `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key

# Groq API
GROQ_API_KEY=your_groq_api_key

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Flask Configuration
FLASK_DEBUG=False
```

2. Replace the placeholder values with your actual Supabase credentials

### Step 4: Create Database Tables

1. Go to your Supabase project dashboard
2. Click on **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy and paste this SQL:

```sql
-- Create papers table
CREATE TABLE IF NOT EXISTS papers (
    id BIGSERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    upload_date TIMESTAMPTZ DEFAULT NOW(),
    branch TEXT NOT NULL,
    semester TEXT NOT NULL,
    subject TEXT NOT NULL,
    exam_info JSONB,
    total_questions INTEGER DEFAULT 0
);

-- Create questions table
CREATE TABLE IF NOT EXISTS questions (
    id BIGSERIAL PRIMARY KEY,
    paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    question_number TEXT NOT NULL,
    question_text TEXT NOT NULL,
    marks INTEGER,
    course_outcome TEXT,
    bloom_level TEXT,
    difficulty TEXT DEFAULT 'Medium',
    chapter TEXT,
    topic TEXT,
    question_type TEXT DEFAULT 'Short Answer',
    answer TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_questions_paper ON questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_papers_branch_semester ON papers(branch, semester);
CREATE INDEX IF NOT EXISTS idx_questions_text ON questions USING gin(to_tsvector('english', question_text));

-- Create admin users table for secured uploads
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example: insert an admin user (replace the hash)
-- Generate hash in Python:
-- >>> import bcrypt
-- >>> bcrypt.hashpw(b"your-password", bcrypt.gensalt()).decode("utf-8")
-- Then insert:
-- INSERT INTO admin_users (username, password_hash) VALUES ('admin@eduquest.ai', '<bcrypt-hash>');

-- Enable Row Level Security (RLS)
ALTER TABLE papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (adjust based on your security needs)
CREATE POLICY "Enable read access for all users" ON papers 
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON papers 
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON papers 
    FOR UPDATE USING (true);

CREATE POLICY "Enable delete for all users" ON papers 
    FOR DELETE USING (true);

CREATE POLICY "Enable read access for all users" ON questions 
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON questions 
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON questions 
    FOR UPDATE USING (true);

CREATE POLICY "Enable delete for all users" ON questions 
    FOR DELETE USING (true);
```

5. Click **Run** (or press Ctrl+Enter)
6. You should see "Success. No rows returned"

### Step 5: Verify Tables Created

1. In Supabase dashboard, go to **Table Editor**
2. You should see two tables:
   - `papers`
   - `questions`

### Step 6: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `supabase>=2.0.0` - Supabase Python client
- `psycopg2-binary>=2.9.0` - PostgreSQL adapter
- All other existing dependencies

### Step 7: Test the Connection

Run your Flask server:

```bash
cd backend
python server.py
```

You should see:
```
Supabase Database Schema:
Run the following SQL in your Supabase SQL Editor:
...
Note: Tables should be created in Supabase dashboard SQL Editor
 * Running on http://0.0.0.0:5000
```

## 🎯 What Changed

### Before (SQLite)
- ❌ Local `questions.db` file
- ❌ Limited to single machine
- ❌ No real-time features
- ❌ Manual backups

### After (Supabase)
- ✅ Cloud-hosted PostgreSQL
- ✅ Accessible from anywhere
- ✅ Real-time subscriptions available
- ✅ Automatic backups
- ✅ Better performance & scalability
- ✅ Built-in authentication ready

## 📊 Database Schema

### `papers` Table
| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| filename | TEXT | Uploaded PDF filename |
| upload_date | TIMESTAMPTZ | Upload timestamp |
| branch | TEXT | Engineering branch |
| semester | TEXT | Semester number |
| subject | TEXT | Subject name |
| exam_info | JSONB | Additional exam metadata |
| total_questions | INTEGER | Question count |

### `questions` Table
| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| paper_id | BIGINT | Foreign key to papers |
| question_number | TEXT | Question number |
| question_text | TEXT | Question text |
| marks | INTEGER | Marks allocated |
| course_outcome | TEXT | Course outcome (CO1, CO2, etc.) |
| bloom_level | TEXT | Bloom's taxonomy level |
| difficulty | TEXT | Easy/Medium/Hard |
| chapter | TEXT | Chapter name |
| topic | TEXT | Topic name |
| question_type | TEXT | Type of question |
| answer | TEXT | Answer (optional) |
| created_at | TIMESTAMPTZ | Creation timestamp |

## 🔐 Security Considerations

### Row Level Security (RLS)

The setup includes basic RLS policies that allow public access. **For production**, you should:

1. **Enable Authentication:**
   ```sql
   -- Example: Only allow authenticated users
   CREATE POLICY "Authenticated users can read" ON papers 
       FOR SELECT TO authenticated USING (true);
   ```

2. **Add User-Specific Policies:**
   ```sql
   -- Example: Users can only modify their own papers
   ALTER TABLE papers ADD COLUMN user_id UUID REFERENCES auth.users(id);
   
   CREATE POLICY "Users can update own papers" ON papers 
       FOR UPDATE TO authenticated 
       USING (auth.uid() = user_id);
   ```

3. **Use Service Role Key for Backend:**
   - The service role key bypasses RLS (for server-side operations)
   - Store it securely in `.env` file
   - Never expose it to the frontend

## 🚀 Advanced Features

### Real-Time Subscriptions (Optional)

Supabase supports real-time updates. To enable:

1. **Enable Realtime in Supabase Dashboard:**
   - Go to Database → Replication
   - Enable for `papers` and `questions` tables

2. **Subscribe in Frontend:**
   ```javascript
   import { createClient } from '@supabase/supabase-js'
   
   const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
   
   // Subscribe to new questions
   const subscription = supabase
     .channel('questions')
     .on('postgres_changes', 
       { event: 'INSERT', schema: 'public', table: 'questions' },
       (payload) => console.log('New question!', payload)
     )
     .subscribe()
   ```

### Storage for PDFs (Optional)

Instead of local file storage, use Supabase Storage:

1. Create a bucket in **Storage** section
2. Update upload code to use Supabase Storage API
3. Generate public URLs for uploaded files

## 📖 API Examples

### Upload Question Paper
```python
POST /api/upload-question-paper
Content-Type: multipart/form-data

file: question_paper.pdf
branch: Computer Engineering
semester: 5
subject: Operating Systems
```

### Get All Questions
```python
GET /api/questions?branch=Computer%20Engineering&semester=5&limit=50
```

### Search Questions
```python
GET /api/questions/search?q=process&subject=Operating%20Systems
```

## 🛠️ Troubleshooting

### Error: "Supabase credentials not found"
- Make sure `.env` file exists in `backend/` folder
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are set
- Restart the server after updating `.env`

### Error: "relation 'papers' does not exist"
- Tables not created yet
- Run the SQL schema in Supabase SQL Editor (Step 4)

### Error: "new row violates row-level security policy"
- RLS is enabled but no policy matches
- Check RLS policies in **Authentication** → **Policies**
- Temporarily disable RLS for testing (not recommended for production)

### Connection Issues
- Check your Supabase project is running
- Verify the URL and keys are correct
- Ensure your IP is not blocked (Supabase free tier allows all IPs)

## 📚 Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)

## ✅ Migration Checklist

- [ ] Created Supabase project
- [ ] Copied credentials to `.env` file
- [ ] Created tables via SQL Editor
- [ ] Verified tables in Table Editor
- [ ] Installed Python dependencies
- [ ] Tested server connection
- [ ] Uploaded a test PDF
- [ ] Verified questions saved to Supabase
- [ ] Checked Question Bank displays data

## 🎉 You're All Set!

Your EduQuest.ai project is now powered by Supabase! Enjoy the benefits of a scalable, cloud-hosted database with real-time capabilities.

For questions or issues, check the [Supabase Discord](https://discord.supabase.com/) or open an issue in your repository.
