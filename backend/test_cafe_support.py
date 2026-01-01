"""
Test script for café-support chatbot scenarios

Tests the three main scenarios:
1. Coffee tastes different today
2. Staff need help dialing in
3. Urgent delivery / running out of coffee
"""

import asyncio
import sys
from app.services.inbound.inbound_bot import inbound_bot
from app.utils.logger import logger


class TestCafeSupport:
    """Test café-support scenarios"""
    
    def __init__(self):
        self.test_user_id = "test_user_123"
        self.conversation_history = []
        self.conversation_data = {}
    
    async def send_message(self, user_message: str, scenario_name: str = ""):
        """Send a message and get bot response"""
        if scenario_name:
            print(f"\n{'='*60}")
            print(f"SCENARIO: {scenario_name}")
            print(f"{'='*60}")
        
        print(f"\n👤 USER: {user_message}")
        
        try:
            response = await inbound_bot.process_message(
                user_message=user_message,
                conversation_history=self.conversation_history,
                user_id=self.test_user_id,
                conversation_data=self.conversation_data
            )
            
            print(f"🤖 BOT: {response}")
            
            # Update conversation history
            self.conversation_history.append({"user": user_message})
            self.conversation_history.append({"bot": response})
            
            # Show state
            if self.conversation_data.get("issue_summary"):
                print(f"\n📊 STATE:")
                print(f"   Issue: {self.conversation_data.get('issue_summary')}")
                print(f"   Category: {self.conversation_data.get('issue_category')}")
                print(f"   Questions Asked: {self.conversation_data.get('questions_asked', 0)}")
                print(f"   Ticket Mentioned: {self.conversation_data.get('ticket_mentioned', False)}")
                print(f"   Create Ticket: {self.conversation_data.get('create_ticket', False)}")
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def reset_conversation(self):
        """Reset conversation for new scenario"""
        self.conversation_history = []
        self.conversation_data = {}
        print("\n🔄 Conversation reset\n")
    
    async def test_scenario_1_coffee_tastes_different(self):
        """Test Scenario 1: Coffee tastes different today"""
        self.reset_conversation()
        
        # Initial problem
        await self.send_message(
            "My coffee tastes different today",
            "SCENARIO 1: Coffee Tastes Different"
        )
        
        # Response to clarifying question
        await self.send_message("It's more bitter than usual")
        
        # Acknowledgment of guidance
        await self.send_message("Ok I'll try those checks")
        
        # Confirm support case
        await self.send_message("Yes please create a support case")
        
        # Final acknowledgment (should NOT repeat case info)
        await self.send_message("Thanks")
        
        print("\n✅ Scenario 1 Complete")
        print("Expected: No repeated support case prompts after creation")
    
    async def test_scenario_1_weak_coffee(self):
        """Test Scenario 1 variant: Weak coffee (test correct coffee science)"""
        self.reset_conversation()
        
        await self.send_message(
            "The coffee is coming out weak today",
            "SCENARIO 1 VARIANT: Weak Coffee (Coffee Science Test)"
        )
        
        await self.send_message("It tastes weaker than normal")
        
        print("\n✅ Scenario 1 Variant Complete")
        print("Expected: Bot should suggest grinding FINER (not coarser) for weak coffee")
        print("Coffee Science: Finer grind → slower flow → stronger extraction")
    
    async def test_scenario_2_staff_dialing_in(self):
        """Test Scenario 2: Staff need help dialing in"""
        self.reset_conversation()
        
        await self.send_message(
            "My staff need help dialing in the espresso",
            "SCENARIO 2: Staff Need Help Dialing In"
        )
        
        await self.send_message("The shots are running too fast, like 15 seconds")
        
        await self.send_message("That's helpful")
        
        await self.send_message("Yes, please share with the team")
        
        await self.send_message("Perfect thanks")
        
        print("\n✅ Scenario 2 Complete")
        print("Expected: Simple base recipe provided, no repeated prompts after case creation")
    
    async def test_scenario_3_urgent_delivery(self):
        """Test Scenario 3: Urgent delivery / running out"""
        self.reset_conversation()
        
        await self.send_message(
            "We're about to run out of coffee in a few hours",
            "SCENARIO 3: Urgent Delivery"
        )
        
        await self.send_message("Order #12345, I didn't get any tracking email")
        
        await self.send_message("Thank you")
        
        print("\n✅ Scenario 3 Complete")
        print("Expected: Immediate escalation, no repeated tracking questions")
    
    async def test_scenario_3_missing_delivery(self):
        """Test Scenario 3 variant: Missing delivery"""
        self.reset_conversation()
        
        await self.send_message(
            "My delivery hasn't arrived and I ordered it 3 days ago",
            "SCENARIO 3 VARIANT: Missing Delivery"
        )
        
        await self.send_message("No tracking email received")
        
        print("\n✅ Scenario 3 Variant Complete")
        print("Expected: Priority tone, immediate escalation")
    
    async def test_coffee_science_validation(self):
        """Test coffee science rules are correct"""
        self.reset_conversation()
        
        print("\n" + "="*60)
        print("COFFEE SCIENCE VALIDATION TEST")
        print("="*60)
        
        # Test 1: Bitter coffee
        await self.send_message("My espresso is too bitter")
        response1 = await self.send_message("Yes, very bitter")
        
        print("\n🔬 VALIDATION CHECK 1:")
        if response1 and ("coarser" in response1.lower() or "coarse" in response1.lower()):
            print("✅ PASS: Bot correctly suggests coarser grind for bitter coffee")
        else:
            print("❌ FAIL: Bot should suggest coarser grind for bitter coffee")
        
        self.reset_conversation()
        
        # Test 2: Weak coffee
        await self.send_message("My coffee is too weak")
        response2 = await self.send_message("Yes, it's under-extracted")
        
        print("\n🔬 VALIDATION CHECK 2:")
        if response2 and ("finer" in response2.lower() or "fine" in response2.lower()):
            print("✅ PASS: Bot correctly suggests finer grind for weak coffee")
        else:
            print("❌ FAIL: Bot should suggest finer grind for weak coffee")
        
        if response2 and "coarser" not in response2.lower():
            print("✅ PASS: Bot does NOT suggest coarser grind for weak coffee")
        else:
            print("❌ FAIL: Bot should NEVER suggest coarser grind for weak coffee")
    
    async def test_no_repeated_prompts(self):
        """Test that support case prompts are not repeated"""
        self.reset_conversation()
        
        print("\n" + "="*60)
        print("NO REPEATED PROMPTS TEST")
        print("="*60)
        
        await self.send_message("My grinder is broken")
        await self.send_message("It stopped working this morning")
        await self.send_message("Yes, create a support case please")
        
        # These should NOT mention support case again
        response1 = await self.send_message("Thanks")
        response2 = await self.send_message("Ok")
        
        print("\n🔬 VALIDATION CHECK:")
        has_repeated_case = False
        for response in [response1, response2]:
            if response and any(word in response.lower() for word in ["support case", "ticket", "case", "team will"]):
                has_repeated_case = True
                break
        
        if not has_repeated_case:
            print("✅ PASS: Bot does NOT repeat support case information after creation")
        else:
            print("❌ FAIL: Bot should NOT mention support case after it's already created")
    
    async def run_all_tests(self):
        """Run all test scenarios"""
        print("\n" + "="*60)
        print("CAFÉ-SUPPORT CHATBOT TEST SUITE")
        print("="*60)
        
        try:
            # Scenario tests
            await self.test_scenario_1_coffee_tastes_different()
            await self.test_scenario_1_weak_coffee()
            await self.test_scenario_2_staff_dialing_in()
            await self.test_scenario_3_urgent_delivery()
            await self.test_scenario_3_missing_delivery()
            
            # Validation tests
            await self.test_coffee_science_validation()
            await self.test_no_repeated_prompts()
            
            print("\n" + "="*60)
            print("ALL TESTS COMPLETED")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ TEST SUITE FAILED: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main test runner"""
    tester = TestCafeSupport()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("Starting café-support chatbot tests...")
    print("Note: This requires the backend services to be running\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
