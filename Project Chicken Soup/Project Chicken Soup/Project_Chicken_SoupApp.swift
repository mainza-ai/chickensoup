//
//  Project_Chicken_SoupApp.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

@main
struct Project_Chicken_SoupApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema(versionedSchema: SchemaV1.self)
        let isPreview = ProcessInfo.processInfo.environment["XCODE_RUNNING_FOR_PLAYGROUNDS"] == "1"
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: isPreview)

        do {
            let container = try ModelContainer(
                for: schema,
                migrationPlan: ChickenSoupMigrationPlan.self,
                configurations: [modelConfiguration]
            )
            Task { @MainActor in
                Self.seedMockData(context: container.mainContext)
            }
            return container
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(sharedModelContainer)
    }
    
    @MainActor
    private static func seedMockData(context: ModelContext) {
        // Only seed if no events exist
        let descriptor = FetchDescriptor<TemporalEvent>()
        if let count = try? context.fetchCount(descriptor), count > 0 {
            return
        }
        
        // Seed Branches
        let mainBranch = TimelineBranch(name: "Universe Prime", isActive: true)
        let altBranch = TimelineBranch(name: "Timeline-115 Alpha", isActive: false)
        
        context.insert(mainBranch)
        context.insert(altBranch)
        
        // Seed Events
        let events = [
            TemporalEvent(
                title: "Magenta UFO Crash Recovery",
                eventDescription: "A circular flying craft crash-landed in northern Italy, recovered by Mussolini's secret cabinet.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1933, month: 6, day: 13)) ?? Date(),
                confidence: 0.94,
                source: "Mussolini Archives",
                type: "crash"
            ),
            TemporalEvent(
                title: "Vatican Transfer to USA",
                eventDescription: "Pope Pius XII facilitated the transfer of the 1933 Magenta craft to the United States.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1944, month: 10, day: 24)) ?? Date(),
                confidence: 0.88,
                source: "Vatican Leak",
                type: "testimony"
            ),
            TemporalEvent(
                title: "S-4 Propulsion Research",
                eventDescription: "Bob Lazar worked on back-engineering gravity amplifiers utilizing Element 115.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1989, month: 12, day: 1)) ?? Date(),
                confidence: 0.92,
                source: "Bob Lazar Testimony",
                type: "theory"
            ),
            TemporalEvent(
                title: "Ariel School Encounter",
                eventDescription: "60+ school children in Ruwa, Zimbabwe observed a landed silver craft and two small beings.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1994, month: 9, day: 16)) ?? Date(),
                confidence: 0.98,
                source: "John Mack Studies",
                type: "anomaly"
            ),
            TemporalEvent(
                title: "Varginha Incident",
                eventDescription: "Multiple sightings and capture of extraterrestrial beings by the military in Varginha, Brazil.",
                timestamp: Calendar.current.date(from: DateComponents(year: 1996, month: 1, day: 20)) ?? Date(),
                confidence: 0.96,
                source: "Aldo Rebelo",
                type: "crash"
            )
        ]
        
        for event in events {
            event.branch = mainBranch
            context.insert(event)
        }
        
        // Seed Lore Entities (for graph)
        let entities = [
            LoreEntity(name: "Magenta Crash", type: "Event", summary: "1933 UFO crash in Magenta, Italy.", confidence: 0.94, source: "Mussolini"),
            LoreEntity(name: "Vatican Secret", type: "Concept", summary: "Pope Pius XII's coordination with OSS.", confidence: 0.88, source: "Historical Leak"),
            LoreEntity(name: "Bob Lazar", type: "Person", summary: "S-4 reverse engineering whistleblower.", confidence: 0.90, source: "S-4 Records"),
            LoreEntity(name: "Element 115", type: "Object", summary: "Superheavy element used for gravitational propulsion.", confidence: 0.92, source: "Area 51"),
            LoreEntity(name: "Ariel School", type: "Place", summary: "Location of the 1994 Zimbabwe close encounter.", confidence: 0.98, source: "Mack Archives"),
            LoreEntity(name: "Varginha Recovery", type: "Project", summary: "Joint US-Brazilian military operation.", confidence: 0.96, source: "Brazilian Defense")
        ]
        
        for entity in entities {
            context.insert(entity)
        }
        
        try? context.save()
    }
}
