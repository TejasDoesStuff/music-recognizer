export async function POST(req: Request) {
    const body = await req.json();
    const { link } = body;
  
    if (!link) {
      return new Response(JSON.stringify({ message: 'Link is required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  
    try {
      const response = await fetch('http://localhost:8000/download_audio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ link }),
      });
  
      const data = await response.json();
  
      if (!response.ok) {
        console.error('error: ', data);
        return new Response(JSON.stringify({ error: data.detail }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        });
      }
  
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (error) {
      console.error('error: ', error);
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  }