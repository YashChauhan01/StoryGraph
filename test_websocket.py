import asyncio
import json
import websockets

async def test_story_graph():
    uri = "ws://localhost:8000/ws/manuscript/test-manuscript"
    
    # Sample narrative text (Shakespeare context)
    narrative_data = {
        "text": "In Belmont, Portia and Nerissa discuss the many suitors who have come to win her hand. 'I remember him well,' Nerissa says of Bassanio, 'and I remember him worthy of thy praise.'",
        "chapter": 1,
        "paragraph": 1
    }

    try:
        async with websockets.connect(uri) as websocket:
            print("🔗 Connected to StoryGraph WebSocket...")
            
            # Send the paragraph
            await websocket.send(json.dumps(narrative_data))
            print("📨 Narrative sent. Waiting for AI extraction...")
            
            # Wait for the response
            response = await websocket.recv()
            result = json.loads(response)
            
            print("\n✅ RECEIVE SUCCESS:")
            print(json.dumps(result, indent=2))
            
            if result.get("type") == "entities_extracted":
                entities = result["data"]["entities_extracted"]
                print(f"\nCharacters Found: {', '.join([c['text'] for c in entities['characters']])}")
                print(f"Summary: {entities.get('summary')}")

    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_story_graph())