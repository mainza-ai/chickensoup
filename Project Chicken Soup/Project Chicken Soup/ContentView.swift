//
//  ContentView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \TemporalEvent.timestamp) private var events: [TemporalEvent]
    @Query private var entities: [LoreEntity]
    
    @State private var selectedEvent: TemporalEvent?
    @State private var queryText = ""
    @State private var isStructuredQuery = false
    @State private var showNavigator = true
    
    // Support adaptive size classes
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    
    // Bottom Tab Selection for compact screens
    enum TabSelection: Hashable {
        case timeline
        case graph
        case navigator
    }
    @State private var activeTab: TabSelection = .timeline
    
    var body: some View {
        #if os(macOS)
        desktopLayout
        #else
        if horizontalSizeClass == .compact {
            phoneLayout
        } else {
            desktopLayout
        }
        #endif
    }
    
    // MARK: - Desktop Layout (macOS & iPad)
    private var desktopLayout: some View {
        NavigationSplitView {
            // Sidebar contains interactive 2D node-link Knowledge Graph
            GraphExplorerView()
                .navigationSplitViewColumnWidth(min: 280, ideal: 320, max: 400)
        } detail: {
            ZStack(alignment: .bottom) {
                // Base timeline track
                TimelineView(events: events, selectedEvent: $selectedEvent)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                
                // Floating Query overlay
                VStack {
                    Spacer()
                    QueryOverlayView(text: $queryText, isStructuredQuery: $isStructuredQuery, onSubmit: handleQuerySubmit)
                        .padding(.bottom, 24)
                }
                
                // Floating AI Navigator overlay
                if showNavigator {
                    VStack {
                        HStack {
                            Spacer()
                            AINavigatorView()
                                .padding(.trailing, DesignConstants.standardPadding)
                                .padding(.top, DesignConstants.standardPadding)
                        }
                        Spacer()
                    }
                }
            }
            .toolbar {
                ToolbarItem {
                    Button(action: { showNavigator.toggle() }) {
                        Label("AI Navigator", systemImage: showNavigator ? "brain.headprofile.fill" : "brain.headprofile")
                    }
                }
            }
        }
    }
    
    // MARK: - iPhone Layout
    private var phoneLayout: some View {
        TabView(selection: $activeTab) {
            // Tab 1: Timeline
            NavigationStack {
                ZStack(alignment: .bottom) {
                    TimelineView(events: events, selectedEvent: $selectedEvent)
                        .navigationTitle("Spacetime")
                    
                    QueryOverlayView(text: $queryText, isStructuredQuery: $isStructuredQuery, onSubmit: handleQuerySubmit)
                        .padding(.bottom, 12)
                }
            }
            .tabItem {
                Label("Timeline", systemImage: "clock.fill")
            }
            .tag(TabSelection.timeline)
            
            // Tab 2: Knowledge Graph
            NavigationStack {
                GraphExplorerView()
                    .navigationTitle("Lore Graph")
            }
            .tabItem {
                Label("Lore Graph", systemImage: "circle.grid.hex.fill")
            }
            .tag(TabSelection.graph)
            
            // Tab 3: AI Navigator Settings/Stats
            NavigationStack {
                ScrollView {
                    AINavigatorView()
                        .padding()
                }
                .navigationTitle("AI Engine")
            }
            .tabItem {
                Label("AI Navigator", systemImage: "brain.fill")
            }
            .tag(TabSelection.navigator)
        }
        .tint(DesignConstants.systemOrange)
    }
    
    private func handleQuerySubmit() {
        guard !queryText.isEmpty else { return }
        
        // Simulating the addition of a new dynamic temporal event from AI query response
        withAnimation(DesignConstants.hoverAnimation) {
            let components = queryText.split(separator: " ")
            let eventType = components.contains(where: { $0.lowercased() == "crash" }) ? "crash" : "anomaly"
            let confidence = Double.random(in: 0.85...0.99)
            
            let newEvent = TemporalEvent(
                title: "Inferred: " + queryText,
                eventDescription: "AI resolved timeline parameters and verified structural authenticity.",
                timestamp: Date(),
                confidence: confidence,
                source: "AI Navigator Engine",
                type: eventType
            )
            modelContext.insert(newEvent)
            try? modelContext.save()
            queryText = ""
        }
    }
}

#Preview {
    let container = try! ModelContainer(for: TemporalEvent.self, configurations: ModelConfiguration(isStoredInMemoryOnly: true))
    let context = container.mainContext
    
    let mockEvent = TemporalEvent(
        title: "Varginha Incident",
        eventDescription: "Reports of extraterrestrial crash and retrievals in Brazil.",
        timestamp: Date(),
        confidence: 0.94,
        source: "Aldo Rebelo",
        type: "crash"
    )
    context.insert(mockEvent)
    
    return ContentView()
        .modelContainer(container)
}
