//
//  LiquidGlassView.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

struct LiquidGlassModifier: ViewModifier {
    var cornerRadius: CGFloat = DesignConstants.panelCornerRadius
    var strokeColor: Color = Color.white.opacity(0.4)
    var shadowColor: Color = DesignConstants.glassShadowColor
    
    func body(content: Content) -> some View {
        content
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: cornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(strokeColor, lineWidth: 1)
            )
            .shadow(
                color: shadowColor,
                radius: DesignConstants.glassShadowRadius,
                x: 0,
                y: DesignConstants.glassShadowOffset.y
            )
    }
}

extension View {
    func liquidGlass(
        cornerRadius: CGFloat = DesignConstants.panelCornerRadius,
        strokeColor: Color = Color.white.opacity(0.4),
        shadowColor: Color = DesignConstants.glassShadowColor
    ) -> some View {
        modifier(LiquidGlassModifier(cornerRadius: cornerRadius, strokeColor: strokeColor, shadowColor: shadowColor))
    }
}
