//
//  DesignConstants.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

enum DesignConstants {
    // MARK: - iOS & Apple.com Style Palette
    static let warmBackground = Color(red: 242/255, green: 242/255, blue: 247/255) // iOS systemGroupedBackground #F2F2F7
    static let primaryText = Color(red: 29/255, green: 29/255, blue: 31/255)      // Apple primary text #1D1D1F
    static let secondaryText = Color(red: 110/255, green: 110/255, blue: 115/255) // Apple secondary text #6E6E73
    
    // Pure iOS System Tint Colors
    static let systemOrange = Color.orange // #FF9500
    static let systemBlue = Color.blue     // #007AFF
    static let systemGreen = Color.green   // #34C759
    static let systemPurple = Color.purple // #AF52DE
    static let systemRed = Color.red       // #FF3B30
    
    // MARK: - Radius
    static let panelCornerRadius: CGFloat = 16
    static let buttonCornerRadius: CGFloat = 10
    static let cardCornerRadius: CGFloat = 14
    
    // MARK: - Spacing & Padding
    static let standardPadding: CGFloat = 16
    static let compactPadding: CGFloat = 8
    static let loosePadding: CGFloat = 24
    
    // MARK: - Shadows
    static let glassShadowRadius: CGFloat = 10
    static let glassShadowOffset = CGPoint(x: 0, y: 4)
    static let glassShadowColor = Color.black.opacity(0.08)
    
    static let activeShadowRadius: CGFloat = 16
    static let activeShadowColor = Color.orange.opacity(0.15)
    
    // MARK: - Animations
    static let hoverAnimation = Animation.spring(response: 0.3, dampingFraction: 0.7)
    static let thinkingAnimation = Animation.easeInOut(duration: 2.0).repeatForever(autoreverses: true)
}
