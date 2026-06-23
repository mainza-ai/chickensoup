import SwiftUI

#if os(macOS)
import AppKit
#else
import UIKit
#endif

extension Color {
    static func dynamicRGB(
        lightRed: Double, lightGreen: Double, lightBlue: Double, lightAlpha: Double = 1.0,
        darkRed: Double, darkGreen: Double, darkBlue: Double, darkAlpha: Double = 1.0
    ) -> Color {
        #if os(macOS)
        let nsColor = NSColor(name: nil) { appearance in
            if appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua {
                return NSColor(red: darkRed, green: darkGreen, blue: darkBlue, alpha: darkAlpha)
            } else {
                return NSColor(red: lightRed, green: lightGreen, blue: lightBlue, alpha: lightAlpha)
            }
        }
        return Color(nsColor: nsColor)
        #else
        let uiColor = UIColor { traitCollection in
            if traitCollection.userInterfaceStyle == .dark {
                return UIColor(red: darkRed, green: darkGreen, blue: darkBlue, alpha: darkAlpha)
            } else {
                return UIColor(red: lightRed, green: lightGreen, blue: lightBlue, alpha: lightAlpha)
            }
        }
        return Color(uiColor: uiColor)
        #endif
    }
    
    static func dynamic(light: Color, dark: Color) -> Color {
        #if os(macOS)
        let nsColor = NSColor(name: nil) { appearance in
            if appearance.bestMatch(from: [.aqua, .darkAqua]) == .darkAqua {
                return NSColor(dark)
            } else {
                return NSColor(light)
            }
        }
        return Color(nsColor: nsColor)
        #else
        let uiColor = UIColor { traitCollection in
            return traitCollection.userInterfaceStyle == .dark ? UIColor(dark) : UIColor(light)
        }
        return Color(uiColor: uiColor)
        #endif
    }
}

enum DesignConstants {
    // MARK: - iOS & Apple.com Style Palette
    static let warmBackground = Color.dynamicRGB(
        lightRed: 242/255, lightGreen: 242/255, lightBlue: 247/255,
        darkRed: 18/255, darkGreen: 18/255, darkBlue: 20/255
    )
    static let primaryText = Color.dynamicRGB(
        lightRed: 29/255, lightGreen: 29/255, lightBlue: 31/255,
        darkRed: 245/255, darkGreen: 245/255, darkBlue: 247/255
    )
    static let secondaryText = Color.dynamicRGB(
        lightRed: 110/255, lightGreen: 110/255, lightBlue: 115/255,
        darkRed: 174/255, darkGreen: 174/255, darkBlue: 178/255
    )
    
    // Custom adaptive card background (white in light mode, dark gray in dark mode)
    static let cardBackground = Color.dynamicRGB(
        lightRed: 1.0, lightGreen: 1.0, lightBlue: 1.0,
        darkRed: 28/255, darkGreen: 28/255, darkBlue: 30/255
    )
    
    // Panel background (glass-like overlay)
    static let panelBackground = Color.dynamic(
        light: Color.white.opacity(0.8),
        dark: Color.black.opacity(0.6)
    )
    
    // Control background for buttons & inputs
    static let controlBackground = Color.dynamic(
        light: Color.black.opacity(0.04),
        dark: Color.white.opacity(0.1)
    )
    
    // Dynamic border/divider color
    static let dividerColor = Color.dynamic(
        light: Color.black.opacity(0.12),
        dark: Color.white.opacity(0.15)
    )
    
    // Glassmorphism borders & shadows
    static let glassBorderColor = Color.dynamic(
        light: Color.white.opacity(0.5),
        dark: Color.white.opacity(0.2)
    )
    static let glassShadowColor = Color.dynamic(
        light: Color.black.opacity(0.14),
        dark: Color.black.opacity(0.4)
    )
    
    // Pure iOS System Tint Colors
    static let systemOrange = Color.orange // #FF9500
    static let systemOrangeText = Color.dynamicRGB(
        lightRed: 230/255, lightGreen: 81/255, lightBlue: 0/255,
        darkRed: 255/255, darkGreen: 159/255, darkBlue: 10/255 // Vibrant Orange #FF9F0A
    )
    static let systemBlue = Color.blue     // #007AFF
    static let systemGreen = Color.green   // #34C759
    static let systemGreenText = Color.dynamicRGB(
        lightRed: 30/255, lightGreen: 107/255, lightBlue: 48/255,
        darkRed: 48/255, darkGreen: 209/255, darkBlue: 88/255 // Vibrant Green #30D158
    )
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
    static let glassShadowRadius: CGFloat = 12
    static let glassShadowOffset = CGPoint(x: 0, y: 6)
    
    static let activeShadowRadius: CGFloat = 16
    static let activeShadowColor = Color.orange.opacity(0.15)
    
    // MARK: - Animations
    static let hoverAnimation = Animation.spring(response: 0.3, dampingFraction: 0.7)
    static let thinkingAnimation = Animation.easeInOut(duration: 2.0).repeatForever(autoreverses: true)
}
