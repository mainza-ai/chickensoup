//
//  TimelineBranch.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import Foundation
import SwiftData

@Model
final class TimelineBranch: Identifiable {
    var id: UUID
    var name: String
    var isActive: Bool
    
    @Relationship(deleteRule: .cascade, inverse: \TemporalEvent.branch) var events: [TemporalEvent]?
    
    init(id: UUID = UUID(), name: String, isActive: Bool = true) {
        self.id = id
        self.name = name
        self.isActive = isActive
        self.events = []
    }
}
