using Graphs
using FeedbackArcSets

function read_from_file(path)
    open(path) do file
        N = parse(Int, readline(file))
        nodes = [readline(file) for i = 1:N]
        M = parse(Int, readline(file))
        edges = Vector{Tuple{Int,Int}}(undef, M)
        for i = 1:M
            edge = split(readline(file))
            edges[i] = (parse(Int, edge[1]) + 1, parse(Int, edge[2]) + 1)
        end
        return nodes, edges
    end
end

function print_problematic_edges(V, E; color = :normal, bold = false)
    nodes_to_edges = Dict{String,Vector{String}}()

    for (from, to) in E
        if !haskey(nodes_to_edges, V[from])
            nodes_to_edges[V[from]] = []
        end
        push!(nodes_to_edges[V[from]], V[to])
    end

    for node in sort!(collect(keys(nodes_to_edges)))
        edges = nodes_to_edges[node]
        node = replace(node, "." => "/")
        printstyled("$node imports: $(join(edges, ", "))\n", bold = bold, color = color)
    end
end

pl(num, singular, plural = singular * "s") = num == 1 ? singular : plural

function solve(old_graph, new_graph)
    # Original graph
    V, E = read_from_file(old_graph)
    G = SimpleDiGraph(Edge.(E))

    # Slightly perturbed graph due to code changes
    Ṽ, Ẽ = read_from_file(new_graph)
    G̃ = SimpleDiGraph(Edge.(Ẽ))

    # Compute the feedback arc set for both graphs
    G_fas = find_feedback_arc_set(G, self_loops = "include", log_level = 0)
    G̃_fas = find_feedback_arc_set(G̃, self_loops = "include", log_level = 0)

    before = length(G_fas.feedback_arc_set)
    after = length(G̃_fas.feedback_arc_set)
    difference = after - before

    if difference == 0
        printstyled(
            "The overall number of problematic import statements stayed the same: $(after)",
            color = :green,
            bold = true,
        )
    elseif difference < 0
        printstyled(
            "The overall number of problematic import statements decreased by $(-difference) from $(before) to $(after)",
            color = :green,
            bold = true,
        )
    else
        printstyled(
            "The overall number of problematic import statements increased by $(difference) from $(before) to $(after)",
            color = :red,
            bold = true,
        )
    end
    print(".")

    if difference > 0
        # Create the graph Ĝ = (Ṽ, Ẽ \ G_fas), and compute the feedback arc set for it
        excluded_edges_by_name = Set{Tuple{String,String}}()
        for (from, to) in G_fas.feedback_arc_set
            push!(excluded_edges_by_name, (V[from], V[to]))
        end
        Ê = filter(edge -> !((Ṽ[edge[1]], Ṽ[edge[2]]) in excluded_edges_by_name), Ẽ)
        Ĝ = SimpleDiGraph(Edge.(Ê))
        Ĝ_fas = find_feedback_arc_set(Ĝ, self_loops = "include", log_level = 0)

        println(" This is likely a direct consequence of the following import \
                $(pl(length(Ĝ_fas.feedback_arc_set), "statement")):\n")
        print_problematic_edges(Ṽ, Ĝ_fas.feedback_arc_set, color = :red)

        # Inform the user that it might be more efficient to remove different import statements,
        # if the FAS of (perturbed - FAS of original) is larger than the FAS of the perturbed graph
        difference_nonoptimal = length(Ĝ_fas.feedback_arc_set)
        if difference_nonoptimal > difference
            println(
                "\nHowever, instead of removing $(difference_nonoptimal) import \
                $(pl(difference_nonoptimal, "statement")), it is sufficient to remove only \
                $(difference) import $(pl(difference, "statement")) from \
                the following list:\n\n",
            )

            print_problematic_edges(Ṽ, G̃_fas.feedback_arc_set, color = :normal)
        else
            printstyled(
                "\n\nAll import cycles are broken by removing the following import statements:\n\n",
                color = :light_black,
            )
            print_problematic_edges(V, G̃_fas.feedback_arc_set, color = :light_black)
        end

        exit(1)
    end

    printstyled(
        "\n\nAll import cycles are broken by removing the following import statements:\n\n",
        color = :light_black,
    )
    print_problematic_edges(V, G̃_fas.feedback_arc_set, color = :light_black)

end

solve(ARGS[1], ARGS[2])
