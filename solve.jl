using Graphs
using FeedbackArcSets

function read_from_file()
    open(ARGS[1]) do file
        N = parse(Int, readline(file))
        nodes = [readline(file) for i in 1:N]
        M = parse(Int, readline(file))
        edges = Vector{Tuple{Int, Int}}(undef, M)
        for i in 1:M
            edge = split(readline(file))
            edges[i] = (parse(Int, edge[1]) + 1, parse(Int, edge[2]) + 1)
        end
        return nodes, edges
    end
end

function solve()
    nodes, edges = read_from_file()
    g = SimpleDiGraph(Edge.(edges))

    result = find_feedback_arc_set(g, self_loops="include")

    nodes_to_edges = Dict{String, Vector{String}}()

    for (from, to) in result.feedback_arc_set
        if !haskey(nodes_to_edges, nodes[from])
            nodes_to_edges[nodes[from]] = []
        end
        push!(nodes_to_edges[nodes[from]], nodes[to])
    end

    println("edges to delete: $(length(result.feedback_arc_set))")
    for node in sort!(collect(keys(nodes_to_edges)))
        edges = nodes_to_edges[node]
        node = replace(node, "." => "/")
        println("$node: $(join(edges, " "))")
    end
end

solve()
