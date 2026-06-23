//
//  Project_Chicken_SoupTests.swift
//  Project Chicken SoupTests
//
//  Created by mck on 6/22/26.
//

import Testing
import Foundation
@testable import Project_Chicken_Soup

struct Project_Chicken_SoupTests {
    
    @Test func testTemporalEventInitialization() {
        let date = Date()
        let event = TemporalEvent(
            title: "Test Event",
            eventDescription: "This is a test description",
            timestamp: date,
            confidence: 0.95,
            source: "Test Source",
            type: "anomaly"
        )
        
        #expect(event.title == "Test Event")
        #expect(event.eventDescription == "This is a test description")
        #expect(event.timestamp == date)
        #expect(event.confidence == 0.95)
        #expect(event.source == "Test Source")
        #expect(event.type == "anomaly")
    }
    
    @Test func testTimelineBranchInitialization() {
        let branch = TimelineBranch(name: "Test Branch", isActive: true)
        
        #expect(branch.name == "Test Branch")
        #expect(branch.isActive == true)
        #expect(branch.events?.isEmpty == true)
    }
    
    @Test func testLoreEntityInitialization() {
        let entity = LoreEntity(
            name: "Test Entity",
            type: "Person",
            summary: "This is a test summary",
            confidence: 0.90,
            source: "Test Source"
        )
        
        #expect(entity.name == "Test Entity")
        #expect(entity.type == "Person")
        #expect(entity.summary == "This is a test summary")
        #expect(entity.confidence == 0.90)
        #expect(entity.source == "Test Source")
    }
}
