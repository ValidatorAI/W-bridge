
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

app.post('/webhook', async (req, res) => {
  // 1. Acknowledge webhook immediately to Campfire
  res.status(200).send('OK');

  try {
    const payload = req.body;

    // 2. Extract html raw content directly as requested
    const rawContent = payload?.message?.body?.html || '';

    if (typeof rawContent !== 'string' || !rawContent.trim()) {
      console.log('⚠ Empty message or missing html body. Skipping.');
      return;
    }

    console.log(`[Raw HTML Received]: "${rawContent}"`);

    // 3. Extract target endpoint from room path
    const roomPath = payload?.room?.path; // e.g., "/rooms/1/3-au15GnHrzQJY/messages"
    if (!roomPath) {
      console.error('❌ Room path missing in payload');
      return;
    }

    const targetUrl = `https://chat.nvgtrs.io${roomPath}`;
    
    // Clean HTML tags and decode basic entities (if passing clean text to an AI model)
    const cleanedText = rawContent
      .replace(/<[^>]*>/g, '') // Strips HTML tags like <div>, <action-text-attachment>, <span>, <img>
      .replace(/&nbsp;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

//    const botReply = `🤖 AI Response to ${payload?.user?.name || 'User'}: I received "${cleanedText}"`;
const botReply = `🤖 AI Response to ${payload?.user?.name || 'User'}: I received ${cleanedText}`;
    console.log(`Sending reply to: ${targetUrl}`);

    // 4. Send payload back to Campfire using 'body'
    await axios.post(
      targetUrl,
       botReply ,
      {
        headers: {
          'Content-Type': 'application/json',
          // 'Authorization': 'Bearer YOUR_CAMPFIRE_API_TOKEN' // Uncomment if needed
        }
      }
    );

    console.log('✅ Posted reply to Campfire successfully!');

  } catch (error) {
    // 5. Log error only — NO res.send() here to prevent ERR_HTTP_HEADERS_SENT
    console.error('❌ Post Error:', error.response?.status, error.response?.data || error.message);
  }
});

app.listen(4141, () => {
  console.log('Server running on port 4141');
});

