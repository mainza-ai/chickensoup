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
    @State private var showIngestion = false
    
    // Inject services
    @StateObject private var backendService = BackendService.shared
    @StateObject private var discoveryService = LLMDiscoveryService.shared
    
    // Support adaptive size classes
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    
    // Bottom Tab Selection for compact screens
    enum TabSelection: Hashable {
        case timeline
        case graph
        case navigator
        case ingest
    }
    @State private var activeTab: TabSelection = .timeline
    
    var body: some View {
        #if os(macOS)
        desktopLayout
            .task {
                await fetchInitialData()
            }
        #else
        Group {
            if horizontalSizeClass == .compact {
                phoneLayout
            } else {
                desktopLayout
            }
        }
        .task {
            await fetchInitialData()
        }
        #endif
    }
    
    private func fetchInitialData() async {
        await backendService.fetchTemporalEvents(context: modelContext)
        await backendService.fetchLoreEntities(context: modelContext)
        await discoveryService.discoverActiveModels()
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
                TemporalTimelineView(events: events, selectedEvent: $selectedEvent)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                
                // Floating Query overlay
                VStack {
                    Spacer()
                    HStack {
                        Spacer()
                        QueryOverlayView(text: $queryText, isStructuredQuery: $isStructuredQuery, onSubmit: handleQuerySubmit)
                        Spacer()
                        
                        if showNavigator {
                            Spacer()
                                .frame(width: 320 + DesignConstants.standardPadding)
                        }
                    }
                    .padding(.bottom, 24)
                }
                .frame(maxWidth: .infinity)
                
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
                ToolbarItem(placement: .primaryAction) {
                    Button(action: { showIngestion.toggle() }) {
                        Label("Ingest Data", systemImage: "doc.badge.plus")
                    }
                }
                ToolbarItem {
                    Button(action: { showNavigator.toggle() }) {
                        Label("AI Navigator", systemImage: "brain")
                    }
                }
            }
            .sheet(isPresented: $showIngestion) {
                NavigationStack {
                    DataIngestionView()
                        .toolbar {
                            ToolbarItem(placement: .cancellationAction) {
                                Button("Close") { showIngestion = false }
                            }
                        }
                }
                .frame(minWidth: 500, minHeight: 600)
            }
        }
    }
    
    // MARK: - iPhone Layout
    private var phoneLayout: some View {
        TabView(selection: $activeTab) {
            // Tab 1: Timeline
            NavigationStack {
                ZStack(alignment: .bottom) {
                    TemporalTimelineView(events: events, selectedEvent: $selectedEvent)
                        .navigationTitle("Spacetime")
                    
                    VStack {
                        Spacer()
                        HStack {
                            Spacer()
                            QueryOverlayView(text: $queryText, isStructuredQuery: $isStructuredQuery, onSubmit: handleQuerySubmit)
                            Spacer()
                        }
                        .padding(.bottom, 12)
                    }
                    .frame(maxWidth: .infinity)
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
            
            // Tab 4: Data Ingest
            NavigationStack {
                DataIngestionView()
            }
            .tabItem {
                Label("Ingest", systemImage: "doc.badge.plus")
            }
            .tag(TabSelection.ingest)
        }
        .tint(DesignConstants.systemOrange)
    }
    
    private func handleQuerySubmit() {
        guard !queryText.isEmpty else { return }
        
        Task {
            _ = await backendService.submitQuery(queryText, isStructured: isStructuredQuery, context: modelContext)
            await MainActor.run {
                withAnimation(DesignConstants.hoverAnimation) {
                    queryText = ""
                }
            }
        }
    }
}

struct ContentView_PreviewHelper: View {
    let container: ModelContainer
    
    init() {
        let schema = Schema([
            TemporalEvent.self,
            TimelineBranch.self,
            LoreEntity.self
        ])
        let container = try! ModelContainer(for: schema, configurations: [ModelConfiguration(isStoredInMemoryOnly: true)])
        let context = container.mainContext
        
        let mainBranch = TimelineBranch(name: "Universe Prime", isActive: true)
        context.insert(mainBranch)
        
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
        
        self.container = container
    }
    
    var body: some View {
        ContentView()
            .modelContainer(container)
    }
}

#Preview {
    ContentView_PreviewHelper()
}
