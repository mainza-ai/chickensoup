//
//  TemporalEvent.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import Foundation
import SwiftData

@Model
final class TemporalEvent: Identifiable {
    var id: UUID
    var title: String
    var eventDescription: String
    var timestamp: Date
    var confidence: Double
    var source: String
    var type: String // "crash", "testimony", "anomaly", "theory"
    var userNotes: String
    var sourcesRaw: String = ""
    
    var sources: [String] {
        get {
            sourcesRaw.components(separatedBy: "|||").filter { !$0.isEmpty }
        }
        set {
            sourcesRaw = newValue.joined(separator: "|||")
        }
    }
    
    var branch: TimelineBranch?
    
    init(
        id: UUID = UUID(),
        title: String,
        eventDescription: String,
        timestamp: Date,
        confidence: Double,
        source: String,
        type: String,
        userNotes: String = "",
        sources: [String] = []
    ) {
        self.id = id
        self.title = title
        self.eventDescription = eventDescription
        self.timestamp = timestamp
        self.confidence = confidence
        self.source = source
        self.type = type
        self.userNotes = userNotes
        let actualSources = sources.isEmpty ? [source] : sources
        self.sourcesRaw = actualSources.joined(separator: "|||")
    }
}
