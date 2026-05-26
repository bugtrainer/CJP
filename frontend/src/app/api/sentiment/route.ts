import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { posts } = await req.json();

    if (!posts || !Array.isArray(posts) || posts.length === 0) {
      return NextResponse.json({ error: 'No posts provided' }, { status: 400 });
    }

    const apiKey = process.env.QWEN_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'QWEN_API_KEY is not set' }, { status: 500 });
    }

    // Filter to news or relevant posts and limit to the most recent 10 posts
    const recentPosts = posts
      .slice(0, 10)
      .map((p: any) => `[${p.time || 'recent'}] ${p.author || 'unknown'}: ${p.title || ''} - ${p.content || ''}`)
      .join('\n\n');

    const prompt = `
Analyze the following recent news and social media posts regarding the 'Cockroach Janta Party' (CJP) movement.
Determine the overall sentiment distribution based on these recent posts, and provide a brief 2-3 sentence insight into the current narrative.

Recent Posts:
${recentPosts}

Provide the response strictly in the following JSON format (no markdown blocks, just raw JSON):
{
  "sentiment": {
    "positive": 45,
    "neutral": 35,
    "negative": 20
  },
  "insight": "Your 2-3 sentence brief analysis goes here."
}
`;

    // Using the Qwen compatible mode endpoint
    const response = await fetch('https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'qwen-max', 
        messages: [
          { role: 'system', content: 'You are an expert AI social media analyst. You must only respond in strictly valid JSON format.' },
          { role: 'user', content: prompt }
        ],
        response_format: { type: "json_object" }
      }),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error("Qwen API Error:", errorData);
      return NextResponse.json({ error: 'Failed to fetch from Qwen API' }, { status: response.status });
    }

    const data = await response.json();
    let content = data.choices[0].message.content;
    
    // Clean up potential markdown formatting if the model still includes it
    content = content.replace(/```json/g, '').replace(/```/g, '').trim();
    
    const parsed = JSON.parse(content);
    return NextResponse.json(parsed);
  } catch (error) {
    console.error("Sentiment Analysis Error:", error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
