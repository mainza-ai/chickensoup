//
//  LoreEntity.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import Foundation
import SwiftData

@Model
final class LoreEntity: Identifiable {
    var id: UUID
    var name: String
    var type: String // "Person", "Place", "Concept", "Object", "Project"
    var summary: String
    var confidence: Double
    var source: String
    
    init(
        id: UUID = UUID(),
        name: String,
        type: String,
        summary: String,
        confidence: Double,
        source: String
    ) {
        self.id = id
        self.name = name
        self.type = type
        self.summary = summary
        self.confidence = confidence
        self.source = source
    }
}
