//
//  SkeletonModifier.swift
//  Project Chicken Soup
//
//  Created by mck on 6/22/26.
//

import SwiftUI

public struct SkeletonModifier: ViewModifier {
    let isLoading: Bool
    @State private var phase: CGFloat = 0.0

    public func body(content: Content) -> some View {
        if isLoading {
            content
                .redacted(reason: .placeholder)
                .overlay(
                    GeometryReader { geo in
                        let size = geo.size
                        LinearGradient(
                            colors: [
                                Color.clear,
                                Color.white.opacity(0.35),
                                Color.clear
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                        .scaleEffect(3)
                        .offset(x: -size.width + (phase * size.width * 2))
                        .blendMode(.screen)
                    }
                )
                .mask(content)
                .onAppear {
                    withAnimation(
                        .linear(duration: 1.5)
                        .repeatForever(autoreverses: false)
                    ) {
                        phase = 1.0
                    }
                }
        } else {
            content
        }
    }
}

public extension View {
    func skeleton(isLoading: Bool) -> some View {
        modifier(SkeletonModifier(isLoading: isLoading))
    }
}
