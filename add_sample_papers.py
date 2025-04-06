from sqlalchemy.orm import Session
from database import SessionLocal, engine, create_tables
from models import Newsletter

# Create tables if they don't exist
create_tables()

# Sample papers data
sample_papers = [
    {
        "title": "Advances in Neural Networks",
        "picture": "/images/paper1.jpg",
        "description": "Recent developments in neural network architectures and their applications in various domains.",
        "content": """# Advances in Neural Networks

Neural networks have seen significant advancements in recent years. This paper explores the latest architectures and their applications in various domains including computer vision, natural language processing, and reinforcement learning.

## Introduction

Neural networks are computational models inspired by the human brain. They consist of interconnected nodes or "neurons" that process and transmit information. Over the years, neural networks have evolved from simple perceptrons to complex architectures like Convolutional Neural Networks (CNNs), Recurrent Neural Networks (RNNs), and Transformers.

## Recent Developments

### Transformer Architecture

The Transformer architecture, introduced in the paper "Attention is All You Need," has revolutionized natural language processing. It relies on self-attention mechanisms to process input sequences in parallel, making it more efficient than traditional RNNs.

### Vision Transformers

Vision Transformers (ViT) apply the Transformer architecture to image processing tasks. Unlike CNNs, ViTs treat images as sequences of patches and process them using self-attention mechanisms.

### Graph Neural Networks

Graph Neural Networks (GNNs) extend neural networks to graph-structured data. They have applications in social network analysis, molecular property prediction, and recommendation systems.

## Applications

### Healthcare

Neural networks are being used for medical image analysis, disease diagnosis, and drug discovery. They can identify patterns in medical data that might be missed by human experts.

### Autonomous Vehicles

Self-driving cars use neural networks for object detection, path planning, and decision making. These networks process data from various sensors to navigate safely.

### Natural Language Processing

Language models like GPT-3 and BERT use neural networks to understand and generate human language. They power applications like chatbots, translation services, and content generation tools.

## Conclusion

Neural networks continue to evolve and find applications in diverse fields. As computational resources become more accessible, we can expect even more sophisticated architectures and applications in the future.
"""
    },
    {
        "title": "Quantum Computing Fundamentals",
        "picture": "/images/paper2.jpg",
        "description": "An introduction to quantum computing principles and their potential impact on computational problems.",
        "content": """# Quantum Computing Fundamentals

Quantum computing represents a paradigm shift in computational capabilities. This paper introduces the fundamental principles of quantum computing and discusses its potential impact on solving complex computational problems.

## Introduction

Quantum computing leverages the principles of quantum mechanics to perform computations. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or qubits, which can exist in multiple states simultaneously due to superposition.

## Quantum Principles

### Superposition

Superposition allows qubits to exist in multiple states at once. This property enables quantum computers to explore multiple solutions simultaneously, potentially leading to exponential speedup for certain problems.

### Entanglement

Entanglement is a quantum phenomenon where qubits become correlated in such a way that the state of one qubit cannot be described independently of the others. This property is crucial for quantum algorithms.

### Quantum Gates

Quantum gates are the building blocks of quantum circuits. They manipulate qubits to perform computations. Common gates include the Hadamard gate, CNOT gate, and Pauli gates.

## Quantum Algorithms

### Shor's Algorithm

Shor's algorithm can efficiently factor large numbers, which could potentially break RSA encryption. This has significant implications for cybersecurity.

### Grover's Algorithm

Grover's algorithm provides a quadratic speedup for unstructured search problems. It can find a specific item in an unsorted database in O(√N) time, compared to O(N) for classical algorithms.

### Quantum Machine Learning

Quantum machine learning combines quantum computing with machine learning techniques. It has the potential to accelerate training and improve the performance of machine learning models.

## Challenges and Future Directions

### Quantum Error Correction

Quantum systems are highly susceptible to noise and decoherence. Quantum error correction techniques are essential for building reliable quantum computers.

### Scalability

Building large-scale quantum computers with many qubits remains a significant challenge. Researchers are exploring various physical implementations, including superconducting circuits, trapped ions, and topological qubits.

### Quantum Supremacy

Quantum supremacy refers to the point where quantum computers can solve problems that are practically impossible for classical computers. Google claimed to achieve quantum supremacy in 2019, but the debate continues.

## Conclusion

Quantum computing is still in its early stages, but it holds tremendous promise for solving complex problems in cryptography, optimization, materials science, and more. As the technology matures, we can expect it to transform various fields and open new frontiers in computing.
"""
    },
    {
        "title": "Climate Change Mitigation Strategies",
        "picture": "/images/paper3.jpg",
        "description": "A comprehensive review of current and emerging strategies to mitigate climate change effects.",
        "content": """# Climate Change Mitigation Strategies

Climate change poses one of the greatest challenges to humanity. This paper reviews current and emerging strategies to mitigate its effects, focusing on technological innovations, policy frameworks, and behavioral changes.

## Introduction

Climate change, primarily driven by greenhouse gas emissions from human activities, is causing global warming, sea level rise, and extreme weather events. Mitigating these effects requires a multi-faceted approach involving governments, industries, and individuals.

## Technological Solutions

### Renewable Energy

Transitioning from fossil fuels to renewable energy sources like solar, wind, and hydropower is crucial for reducing carbon emissions. Recent advancements have made these technologies more efficient and cost-effective.

### Carbon Capture and Storage

Carbon capture and storage (CCS) technologies capture CO2 emissions from power plants and industrial facilities and store them underground. Direct air capture (DAC) systems can remove CO2 directly from the atmosphere.

### Energy Efficiency

Improving energy efficiency in buildings, transportation, and industrial processes can significantly reduce energy consumption and associated emissions. Smart grids, LED lighting, and electric vehicles are examples of energy-efficient technologies.

## Policy Frameworks

### Carbon Pricing

Carbon taxes and cap-and-trade systems put a price on carbon emissions, incentivizing businesses and individuals to reduce their carbon footprint. These market-based approaches can be effective when properly implemented.

### Regulatory Measures

Regulations on emissions standards, fuel efficiency, and renewable energy mandates can drive the adoption of low-carbon technologies. Building codes and land-use planning can also promote sustainable development.

### International Cooperation

Global agreements like the Paris Agreement provide a framework for international cooperation on climate change mitigation. They set targets for emissions reductions and mechanisms for financial and technological support.

## Behavioral Changes

### Sustainable Consumption

Changing consumption patterns, such as reducing meat consumption, minimizing waste, and choosing sustainable products, can reduce individual carbon footprints.

### Transportation Choices

Using public transportation, carpooling, cycling, or walking instead of driving alone can significantly reduce transportation-related emissions.

### Community Engagement

Community-based initiatives can promote sustainable practices and create social norms around environmental stewardship.

## Emerging Approaches

### Nature-Based Solutions

Reforestation, afforestation, and ecosystem restoration can sequester carbon while providing additional benefits like biodiversity conservation and flood protection.

### Geoengineering

Geoengineering approaches, such as solar radiation management and ocean fertilization, aim to manipulate the Earth's climate system to counteract global warming. However, these approaches are controversial due to potential unintended consequences.

### Circular Economy

The circular economy model aims to minimize waste and maximize resource efficiency through recycling, reuse, and regenerative design.

## Conclusion

Mitigating climate change requires a combination of technological innovation, policy intervention, and behavioral change. While the challenge is immense, the growing momentum for climate action provides hope for a sustainable future.
"""
    }
]

# Add sample papers to the database
def add_sample_papers():
    db = SessionLocal()
    try:
        # Check if papers already exist
        existing_papers = db.query(Newsletter).count()
        if existing_papers == 0:
            # Add sample papers
            for paper in sample_papers:
                db_paper = Newsletter(
                    title=paper["title"],
                    picture=paper["picture"],
                    description=paper["description"],
                    content=paper["content"]
                )
                db.add(db_paper)
            db.commit()
            print("Sample papers added successfully!")
        else:
            print(f"Database already contains {existing_papers} papers. No sample papers added.")
    except Exception as e:
        db.rollback()
        print(f"Error adding sample papers: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_papers()
